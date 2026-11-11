"""
Tests for the review-GUI checks in scripts/scan_trigger_conditions.py (PR #58).

The scanner must stay silent on reviews saved by the fixed GUI and flag reviews saved by the
old one. Both are checked on the researcher's real click log (goldens/inputs/pc_line1_10_12_26):
the fixed GUI's saved file is the click-replay golden, and the old GUI is the -1/+1 logic of
FreezingReviewer._update_image as it was on develop before #58, replayed on the raw .dat.
"""

from __future__ import annotations

import importlib.util
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]
GOLDENS = REPO / "tests" / "test_data" / "goldens"
CASE = GOLDENS / "inputs" / "pc_line1_10_12_26"


def _load_scanner():
    spec = importlib.util.spec_from_file_location(
        "scan_trigger_conditions", REPO / "scripts" / "scan_trigger_conditions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look the module up while it loads
    spec.loader.exec_module(module)
    return module


scan = _load_scanner()


def _raw_dat() -> Path:
    dats = [p for p in CASE.glob("*.dat") if "reviewed" not in p.name]
    assert len(dats) == 1
    return dats[0]


def _old_gui_replay(raw: list[int], image_row: dict[str, int], clicks, cap: int):
    """Saved counts and net changes the pre-#58 GUI produced for these clicks."""
    counts, changes = list(raw), [0] * len(raw)
    for image, change in clicks:
        start = image_row[f"Image_{image}.png"]
        if change < 0:
            if counts[start] + change < 0:
                continue
            current = counts[start]
            for i in range(start, 0, -1):
                if counts[i] == current - 1:
                    start = start - i  # the bug: walk distance used as a row label
                    break
        for row in range(start, len(counts)):
            counts[row] = min(max(counts[row] + change, 0), cap)
            changes[row] += change  # logged without allowing for the clip
    return counts, changes


def test_self_test_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert scan._self_test() == 0
    assert "FAIL" not in capsys.readouterr().out


def test_fixed_gui_review_of_real_clicks_is_clean() -> None:
    raw = _raw_dat()
    golden = GOLDENS / "expected" / "test_click_replay" / f"reviewed_{raw.name}"
    result = scan._scan_review(golden, raw, None)
    assert result.reason is None
    assert result.damage == []
    assert result.harmless == []


def test_old_gui_review_of_real_clicks_is_flagged() -> None:
    cfg = tomllib.loads((CASE / "clicks.toml").read_text())
    dat = scan._read_dat(_raw_dat())
    assert dat is not None
    sample, cap = cfg["sample"], cfg["wells_per_sample"]
    raw = [int(float(r[f"Sample_{sample}"])) for r in dat.rows]
    image_row = {r["Picture"].strip(): i for i, r in enumerate(dat.rows) if r["Picture"].strip()}

    saved, changes = _old_gui_replay(raw, image_row, cfg["clicks"], cap)
    hits = scan._find_review_damage(raw, saved, changes, cap, sorted(image_row.values()))

    kinds = {kind for kind, _, _ in hits}
    # the researcher's report: late -1s erased early freezing events
    assert "erased-freeze" in kinds
    erased_starts = [row for kind, row, _ in hits if kind == "erased-freeze"]
    assert max(erased_starts) < 50  # reached back to the start of the run
    # the +1s near the full plate lost wells
    assert "lost-well" in kinds


@pytest.mark.parametrize(
    ("reviewed", "raw"),
    [
        ("reviewed_sgp 5.15.24 a base.dat", "sgp 5.15.24 a base.dat"),
        ("reviewed_sgp 5.15.24 a base(2).dat", "sgp 5.15.24 a base.dat"),
        ("test1_reviewed_sgp 02.21.24 a base.dat", "sgp 02.21.24 a base.dat"),
        ("reviewed_reviewed_sgp blanks.dat", "sgp blanks.dat"),
        ("reviewed.dat", "raw.dat"),
    ],
)
def test_reviewed_file_pairs_with_its_raw_dat(tmp_path: Path, reviewed: str, raw: str) -> None:
    (tmp_path / raw).write_text("")
    (tmp_path / reviewed).write_text("")
    assert scan._raw_partner(tmp_path / reviewed) == tmp_path / raw


def test_reviewed_file_without_raw_dat_is_unpaired(tmp_path: Path) -> None:
    (tmp_path / "reviewed_sgp 5.15.24 a base.dat").write_text("")
    assert scan._raw_partner(tmp_path / "reviewed_sgp 5.15.24 a base.dat") is None
