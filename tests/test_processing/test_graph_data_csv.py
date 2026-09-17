"""Tests for olaf.processing.graph_data_csv.GraphDataCSV.

These cover the three review bugs fixed in the numerical-core overhaul (Milestone A.1):

    #1  ``prev_val == np.nan`` is always False -> use ``pd.isna`` so a pruned (NaN)
        previous value falls back to the one before it.
    #2  ``UnboundLocalError`` when ``last_4_i`` is empty (every accumulated value pruned).
    #8  Lost exception chaining in the column-rename guard (``raise ... from e``).

The larger structural rewrite (extracting the dilution-blending closure into a pure,
independently-tested function) and a human-curated numerical golden for the corrected
output are still pending — see TODO_overhaul.md Milestone A.1 / A.3.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from olaf.processing.graph_data_csv import GraphDataCSV, _select_blended_value

# GraphDataCSV constructor args that are not exercised by these behavioural tests.
_COMMON_KWARGS = dict(
    sample_type="salt",
    vol_air_filt=100.0,
    wells_per_sample=32,
    filter_used=1.0,
    vol_susp=10.0,
)


def _write_frozen(folder: Path, temps: list[float], samples: dict[str, list[int]]) -> Path:
    """Write a minimal ``frozen_at_temp_reviewed_base.csv`` and return its path.

    Columns are ``degC`` followed by the raw frozen-well counts per sample, matching the
    real stage-1 input that GraphDataCSV reads.
    """
    df = pd.DataFrame({"degC": temps, **samples})
    path = folder / "frozen_at_temp_reviewed_base.csv"
    df.to_csv(path, index=False)
    return path


def _make_graph(folder: Path, dilution: dict) -> GraphDataCSV:
    return GraphDataCSV(
        folder,
        num_samples=len(dilution),
        dict_samples_to_dilution=dilution,
        **_COMMON_KWARGS,
    )


# --------------------------------------------------------------------- bug #2


def test_empty_last_4_i_does_not_raise(tmp_path):
    """Bug #2: when the first dilution is entirely pruned (all wells >= 30), the next
    dilution's overlap window ``last_4_i`` is empty. The old code raised
    ``UnboundLocalError``; the fix initialises ``i = -1`` so the next dilution fills the
    whole column instead.
    """
    dilution = {"Sample_0": 1, "Sample_1": 10, "Sample_2": float("inf")}
    temps = [-5.0, -6.0, -7.0, -8.0, -9.0, -10.0, -11.0, -12.0]
    _write_frozen(
        tmp_path,
        temps,
        {
            # dilution 1: every value >= 30 -> pruned to NaN -> empty last_4_i on the
            # transition to dilution 10.
            "Sample_0": [31, 31, 31, 31, 31, 31, 31, 31],
            # dilution 10: valid, increasing, all < 30.
            "Sample_1": [1, 2, 3, 5, 8, 12, 18, 25],
            # background (undiluted): small.
            "Sample_2": [0, 0, 0, 0, 1, 1, 1, 2],
        },
    )
    graph = _make_graph(tmp_path, dilution)

    result = graph.convert_INPs_L("site = SITE", save=False, show_plot=False)

    assert list(result.columns) == ["degC", "dilution", "INPS_L", "lower_CI", "upper_CI"]
    # The wholesale fill replaced the (empty) dilution-1 result with dilution 10.
    filled = result.loc[result["INPS_L"].notna(), "dilution"]
    assert not filled.empty
    assert set(filled.unique()) == {10}


# --------------------------------------------------------------------- bug #1


def test_nan_gap_downswing_uses_fallback_value(tmp_path):
    """Bug #1: when the accumulated spectrum swings down at an index whose ``i - 1``
    neighbour was pruned to NaN, ``prev_val`` at ``i - 1`` is NaN. The fix uses
    ``pd.isna`` to fall back to the real value at ``i - 2``; the old ``== np.nan``
    (always False) silently kept ``prev_val`` NaN, so every comparison fell through and
    the blending logic never fired.

    The input below drives exactly that path (dilution-1 result is non-NaN at indices
    [3, 4, 6, 7] with a dip at index 4 to seed ``going_down`` and a pruned gap at index
    5). We assert the *dilution selection* (a logic outcome, not a scientific magnitude):
    with the fallback active the blending switches indices 6-7 to dilution 10. Verified by
    hand that the buggy code instead leaves them on dilution 1; the corrected numerical
    magnitudes are locked separately by a human-curated golden (pending, see
    TODO_overhaul.md A.3 / Human-Needs-To-Do).
    """
    dilution = {"Sample_0": 1, "Sample_1": 10, "Sample_2": float("inf")}
    temps = [-5.0, -6.0, -7.0, -8.0, -9.0, -10.0, -11.0, -12.0]
    _write_frozen(
        tmp_path,
        temps,
        {
            # dilution 1: up to idx 3, dip at idx 4 (seeds going_down), idx 5 pruned
            # (>= 30 -> NaN gap), recover at idx 6.
            "Sample_0": [2, 4, 6, 10, 7, 31, 12, 15],
            "Sample_1": [1, 2, 4, 6, 9, 13, 19, 26],
            "Sample_2": [0, 0, 0, 0, 0, 0, 1, 1],
        },
    )
    graph = _make_graph(tmp_path, dilution)

    result = graph.convert_INPs_L("site = SITE", save=False, show_plot=False)

    # The interior gap is preserved as NaN.
    assert pd.isna(result.loc[5, "INPS_L"])
    # The fallback (i-2) lets the down-swing blending run and switch to dilution 10;
    # without the fix these rows stay on dilution 1.
    assert result.loc[6, "dilution"] == 10.0
    assert result.loc[7, "dilution"] == 10.0
    # No spurious infinities leaked through (log/division guarded downstream).
    assert not np.isinf(result["INPS_L"].to_numpy(dtype=float)).any()


# --------------------------------------------------------------------- bug #8


def test_rename_failure_chains_original_exception(tmp_path, monkeypatch):
    """Bug #8: the column-rename guard must chain the underlying exception
    (``raise ValueError(...) from e``) so the original cause is not lost.
    """
    dilution = {"Sample_0": 1, "Sample_1": 10, "Sample_2": float("inf")}
    _write_frozen(
        tmp_path,
        [-5.0, -6.0, -7.0],
        {"Sample_0": [1, 2, 3], "Sample_1": [1, 2, 3], "Sample_2": [0, 0, 0]},
    )

    def _boom(*_args, **_kwargs):
        raise RuntimeError("original cause")

    monkeypatch.setattr(pd.DataFrame, "rename", _boom)

    with pytest.raises(ValueError, match="Failed to rename columns") as exc_info:
        _make_graph(tmp_path, dilution)

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) == "original cause"


# ------------------------------------------------ _select_blended_value (pure)


def _blend(**overrides):
    """Call _select_blended_value with sensible defaults, overriding per test."""
    kwargs = dict(
        prev_inp=10.0,
        prev_upper_err=5.0,  # -> prev_bound = 15.0
        curr_inp=8.0,
        curr_lower=3.0,
        curr_upper=6.0,
        curr_dil_upper_at_i=1.0,
        next_inp=9.0,
        next_lower=4.0,
        next_upper=2.0,
    )
    kwargs.update(overrides)
    return _select_blended_value(**kwargs)


def test_blend_both_within_keeps_lower_error_current():
    # prev_bound (15) > curr (8) and > next (9); current has the smaller upper CI
    # (1 < 2) -> keep current.
    assert _blend(curr_dil_upper_at_i=1.0, next_upper=2.0) is None


def test_blend_both_within_takes_lower_error_next():
    # Same "both within" case, but now the next dilution has the smaller upper CI
    # (2 < 3) -> take next.
    assert _blend(curr_dil_upper_at_i=3.0, next_upper=2.0) == (9.0, 4.0, 2.0)


def test_blend_only_current_within_keeps_current():
    # prev_bound (15) > curr (8) but not > next (20) -> keep current.
    assert _blend(curr_inp=8.0, next_inp=20.0) is None


def test_blend_only_next_within_takes_next():
    # prev_bound (15) not > curr (20) but > next (8) -> take next.
    assert _blend(curr_inp=20.0, next_inp=8.0) == (8.0, 4.0, 2.0)


def test_blend_neither_within_averages_with_rms_ci():
    # prev_bound (15) below both curr (20) and next (25) -> average, RMS-propagating CIs.
    inp, lower, upper = _blend(
        curr_inp=20.0, next_inp=25.0, curr_lower=3.0, next_lower=4.0, curr_upper=6.0, next_upper=8.0
    )
    assert inp == 22.5  # (20 + 25) / 2
    assert lower == 2.5  # sqrt(3**2 + 4**2) / 2 = 5 / 2
    assert upper == 5.0  # sqrt(6**2 + 8**2) / 2 = 10 / 2
