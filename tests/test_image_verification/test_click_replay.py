"""
Replay real researcher GUI clicks on raw .dat files, headless (no gui marker).

Each case is a folder under tests/test_data/goldens/inputs/ holding one raw .dat (any
name, not reviewed_*) and a clicks.toml (sample, num_samples, wells_per_sample,
clicks = [[image, change], ...]).
Add a folder to add a case. Rule checked: a click on image N changes image N and later,
never earlier images (regression for the -1 reaching back to the start of the run).
The saved reviewed_*.dat is also compared to the one in goldens/expected/test_click_replay/;
create it with OLAF_REGEN_GOLDEN=1 and have a researcher check it before committing.
"""

from __future__ import annotations

import io
import os
import tomllib
from pathlib import Path

import pandas as pd
import pytest

from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.utils.data_handler import DataHandler

GOLDENS = Path(__file__).parents[1] / "test_data" / "goldens"
INPUTS = GOLDENS / "inputs"
CASES = sorted(INPUTS.glob("*/clicks.toml"))


def _picture(n: int) -> str:
    return f"Image_{n}.png"


def _reviewer(case: Path) -> tuple[FreezingReviewer, dict]:
    """Load the case's raw .dat into a FreezingReviewer without Tk, using the GUI's loader."""
    dats = [p for p in case.parent.glob("*.dat") if "reviewed" not in p.name]
    if len(dats) != 1:
        pytest.skip(f"Need exactly one raw .dat next to {case}, found {len(dats)}")
    with case.open("rb") as f:
        cfg = tomllib.load(f)
    loaded = DataHandler(case.parent, cfg["num_samples"], excludes=("reviewed",))
    app = _headless_reviewer(loaded.data, cfg["num_samples"], cfg["wells_per_sample"])
    app.data_file = loaded.data_file
    return app, cfg


def _headless_reviewer(
    data: pd.DataFrame, num_samples: int, wells_per_sample: int
) -> FreezingReviewer:
    """FreezingReviewer on data without Tk: skip __init__ and stub the two display methods."""
    data["changes"] = [[(0, 0)] * num_samples for _ in range(len(data))]
    app = FreezingReviewer.__new__(FreezingReviewer)
    app.data = data
    app.num_samples = num_samples
    app.wells_per_sample = wells_per_sample
    app.photos = [Path(p) for p in data["Picture"].dropna().unique()]
    app.current_photo_index = 0
    app._uncapped = {}
    app._display_current_temp = lambda *_: None  # type: ignore[method-assign]
    app._display_num_frozen = lambda *_: None  # type: ignore[method-assign]
    return app


def _row(app: FreezingReviewer, n: int) -> int:
    return app.data.index[app.data["Picture"] == _picture(n)][0]


def _click(app: FreezingReviewer, sample: int, n: int, change: int) -> None:
    app.current_photo_index = [p.name for p in app.photos].index(_picture(n))
    app._update_image(sample=sample, change=change)


@pytest.mark.parametrize("case", CASES, ids=[c.parent.name for c in CASES])
def test_each_click_leaves_earlier_images_alone(case: Path) -> None:
    app, cfg = _reviewer(case)
    col = f"Sample_{cfg['sample']}"
    for n, change in cfg["clicks"]:
        before = app.data[col].copy()
        _click(app, cfg["sample"], n, change)
        prev = _row(app, n - 1)
        assert app.data.loc[:prev, col].equals(before.loc[:prev]), (
            f"click {change:+d} at image {n} changed image {n - 1} or earlier"
        )


@pytest.mark.parametrize("case", CASES, ids=[c.parent.name for c in CASES])
def test_counts_at_each_image_match_the_click_log(case: Path) -> None:
    """Each image reads its raw count plus every click up to it (clipped to the well range)."""
    app, cfg = _reviewer(case)
    col = f"Sample_{cfg['sample']}"
    raw = app.data[col].copy()
    clicks = cfg["clicks"]
    for n, change in clicks:
        _click(app, cfg["sample"], n, change)

    for n in range(clicks[0][0] - 1, max(m for m, _ in clicks) + 1):
        if not (app.data["Picture"] == _picture(n)).any():
            continue
        row = _row(app, n)
        expected = raw[row] + sum(c for m, c in clicks if m <= n)
        expected = min(max(expected, 0), cfg["wells_per_sample"])
        assert app.data.loc[row, col] == expected, f"image {n}"
    assert app.data[col].is_monotonic_increasing, "counts drop somewhere between images"


@pytest.mark.parametrize("case", CASES, ids=[c.parent.name for c in CASES])
def test_reviewed_file_matches_golden(case: Path) -> None:
    """Replay the clicks and compare what the GUI would save on close to the checked golden."""
    app, cfg = _reviewer(case)
    for n, change in cfg["clicks"]:
        _click(app, cfg["sample"], n, change)
    # Same output as save_to_new_file(prefix="reviewed", sep="\t"), kept in memory
    reviewed = app.data.to_csv(sep="\t", index=False, lineterminator="\n")

    golden = GOLDENS / "expected" / "test_click_replay" / f"reviewed_{app.data_file.name}"
    if os.environ.get("OLAF_REGEN_GOLDEN"):
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(reviewed)
        pytest.skip(f"regenerated golden: {golden}")
    if not golden.exists():
        pytest.fail(f"Missing golden: {golden}\nRun with OLAF_REGEN_GOLDEN=1 to create it.")
    # Compare as tables first so a mismatch names the row and column, then character for character
    pd.testing.assert_frame_equal(
        pd.read_csv(io.StringIO(reviewed), sep="\t"), pd.read_csv(golden, sep="\t")
    )
    assert reviewed == golden.read_text()


def test_late_well_correction_near_full_plate_keeps_the_well() -> None:
    """
    Given: 4 wells; images 1-4 read 0, 0, 1, 4 (a well froze at image 2 but was seen at 3,
           and the plate is full by image 4).
    When:  +1 on image 2, then -1 on image 3 (the camera catching up).
    Then:  image 4 still reads 4. Regression: capping after the +1 (4 + 1 -> 4) made the -1
           leave it at 3.
    """
    data = pd.DataFrame(
        {
            "Sample_0": [0, 0, 1, 4],
            "Picture": [_picture(n) for n in range(1, 5)],
        }
    )
    app = _headless_reviewer(data, num_samples=1, wells_per_sample=4)
    _click(app, 0, 2, +1)
    _click(app, 0, 3, -1)

    assert app.data["Sample_0"].tolist() == [0, 1, 1, 4]


def test_noisy_dip_below_zero_does_not_swallow_a_later_plus_one() -> None:
    """
    Given: noisy raw counts 0, 1, 0, 0, 1 (a false freeze at image 2).
    When:  -1 on image 2, then +1 on image 4.
    Then:  image 4 shows 1; the -1 doesn't leave a hidden -1 on images 3-4 that eats the +1.
    """
    data = pd.DataFrame(
        {"Sample_0": [0, 1, 0, 0, 1], "Picture": [_picture(n) for n in range(1, 6)]}
    )
    app = _headless_reviewer(data, num_samples=1, wells_per_sample=4)
    _click(app, 0, 2, -1)
    _click(app, 0, 4, +1)

    assert app.data["Sample_0"].tolist() == [0, 0, 0, 1, 1]
