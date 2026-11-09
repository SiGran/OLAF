"""
Replay real researcher GUI clicks on raw .dat files, headless (no gui marker).

Each case is a folder under tests/test_data/goldens/inputs/ holding one raw .dat (any
name, not reviewed_*) and a clicks.toml (sample, num_samples, wells_per_sample,
clicks = [[image, change], ...]).
Add a folder to add a case. Rule checked: a click on image N changes image N and later,
never earlier images (regression for the -1 reaching back to the start of the run). The GUI
can change earlier images only if the researcher confirms it in the previous-image pop-up;
a replay must never trigger that pop-up.
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
    if "changes" not in data:
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
    app.shown_photos = []  # type: ignore[attr-defined]
    app.show_photo = lambda: app.shown_photos.append(app.current_photo_index)  # type: ignore[attr-defined,method-assign]
    app.warnings = []  # type: ignore[attr-defined]
    app._warn = app.warnings.append  # type: ignore[attr-defined,method-assign]
    app.conflicts = []  # type: ignore[attr-defined]

    def ask(message: str, goto_name: str) -> str:
        app.conflicts.append(goto_name)  # type: ignore[attr-defined]
        return "cancel"

    app._ask_minus_one_conflict = ask  # type: ignore[method-assign]
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

    assert app.conflicts == [], "a logged -1 hit the previous-image pop-up"
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


def _synthetic(counts: list[int], wells_per_sample: int = 4) -> FreezingReviewer:
    """One sample, one row per image (Image_1, Image_2, ...)."""
    data = pd.DataFrame(
        {"Sample_0": counts, "Picture": [_picture(n) for n in range(1, len(counts) + 1)]}
    )
    return _headless_reviewer(data, num_samples=1, wells_per_sample=wells_per_sample)


def _tallies(app: FreezingReviewer) -> list[tuple[int, int]]:
    return [row[0] for row in app.data["changes"]]


def test_plus_one_on_a_full_image_is_refused() -> None:
    """+1 on an image already showing wells_per_sample changes nothing and warns."""
    app = _synthetic([0, 2, 4])
    _click(app, 0, 3, +1)

    assert app.data["Sample_0"].tolist() == [0, 2, 4]
    assert _tallies(app) == [(0, 0)] * 3
    assert len(app.warnings) == 1


def test_minus_one_on_a_full_image_with_hidden_wells_shows_one_less() -> None:
    """
    Given: raw 0, 0, 1, 4 on a 4-well plate; two +1s on image 2 (wells seen late) leave image 4
           at 4 shown with 2 more hidden.
    When:  -1 on image 4 (the photo shows 3 frozen).
    Then:  image 4 shows 3, one less than before, in a single click.
    """
    app = _synthetic([0, 0, 1, 4])
    _click(app, 0, 2, +1)
    _click(app, 0, 2, +1)
    assert app.data["Sample_0"].tolist() == [0, 2, 3, 4]

    _click(app, 0, 4, -1)

    assert app.data["Sample_0"].tolist() == [0, 2, 3, 3]
    assert _tallies(app) == [(0, 0), (2, 0), (2, 0), (2, -3)]


@pytest.mark.parametrize(
    ("answer", "counts", "tallies", "photo_index"),
    [
        ("cancel", [0, 1, 1], [(0, 0)] * 3, 2),
        ("goto", [0, 1, 1], [(0, 0)] * 3, 1),
        ("proceed", [0, 0, 0], [(0, 0), (0, -1), (0, -1)], 2),
    ],
)
def test_minus_one_when_previous_image_has_same_count(
    answer: str, counts: list[int], tallies: list[tuple[int, int]], photo_index: int
) -> None:
    """
    Given: images 1-3 read 0, 1, 1, so image 2 (already checked) shows the same count as 3.
    When:  -1 on image 3, and the pop-up is answered.
    Then:  cancel changes nothing; goto changes nothing and opens image 2 (where it rose);
           proceed lowers from the rise on, image 2 included.
    """
    app = _synthetic([0, 1, 1])
    app._ask_minus_one_conflict = lambda *_: answer  # type: ignore[method-assign]
    _click(app, 0, 3, -1)

    assert app.data["Sample_0"].tolist() == counts
    assert _tallies(app) == tallies
    assert app.current_photo_index == photo_index
    assert app.shown_photos == ([1] if answer == "goto" else [])


def test_conflict_with_noisy_dip_points_at_the_previous_image() -> None:
    """
    Given: Image_1 shows 1, a row without a picture dips to 0, Image_2 shows 1 again.
    When:  -1 on Image_2 and "proceed".
    Then:  the pop-up points at Image_1 (not the current image), and both images drop to 0.
    """
    data = pd.DataFrame({"Sample_0": [1, 0, 1], "Picture": [_picture(1), None, _picture(2)]})
    app = _headless_reviewer(data, num_samples=1, wells_per_sample=4)
    asked: list[str] = []

    def ask(message: str, goto_name: str) -> str:
        asked.append(goto_name)
        return "proceed"

    app._ask_minus_one_conflict = ask  # type: ignore[method-assign]
    _click(app, 0, 2, -1)

    assert asked == [_picture(1)]
    assert app.data["Sample_0"].tolist() == [0, 0, 0]


def test_tallies_survive_saving_and_reopening() -> None:
    """
    A reviewed file stores the tallies as text; reopening and clicking continues them, and
    a row from an older file (one net number per sample) is converted as a whole.
    """
    app = _synthetic([0, 1, 2, 3])
    _click(app, 0, 2, +1)
    saved = app.data.to_csv(sep="\t", index=False, lineterminator="\n")

    reopened = _headless_reviewer(pd.read_csv(io.StringIO(saved), sep="\t"), 1, 4)
    _click(reopened, 0, 3, +1)
    assert _tallies(reopened) == [(0, 0), (1, 0), (2, 0), (2, 0)]

    data = pd.DataFrame(
        {"Sample_0": [0, 1], "Sample_1": [0, 0], "Picture": [_picture(1), _picture(2)]}
    )
    data["changes"] = ["[0, 0]", "[1, -1]"]
    legacy = _headless_reviewer(data, num_samples=2, wells_per_sample=4)
    _click(legacy, 0, 2, +1)
    assert legacy.data["changes"].tolist() == [[0, 0], [(2, 0), (0, -1)]]
