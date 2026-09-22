"""Tests for cold-plate DI background resolution (``olaf.processing.di_background``)."""

import warnings

import pandas as pd
import pytest

from olaf.config import MainConfig
from olaf.processing import di_background
from olaf.processing.di_background import (
    combine_di,
    combined_path,
    di_dates,
    find_combined,
    find_frozen_at_temp,
    resolve_di_background,
)


def _write_frozen(folder, name, rows):
    """Write a frozen_at_temp-shaped csv: degC plus two Sample_ columns, no header block."""
    path = folder / name
    pd.DataFrame(rows, columns=["degC", "Sample_0", "Sample_1"]).to_csv(path, index=False)
    return path


def _cold_plate_config(folder, names, di_combined=None):
    for name in names:
        (folder / name).write_text("")
    with warnings.catch_warnings():
        # tmp_path folder names carry no treatment or date, and these tiny fixtures use a
        # 2-sample plate; both trip MainConfig's soft sanity warnings, neither matters here.
        warnings.simplefilter("ignore", UserWarning)
        return MainConfig(
            data_folder=folder,
            site="SITE",
            start_time="2025-07-16 16:20:00",
            end_time="2025-07-16 17:52:00",
            filter_color="white",
            notes="none",
            user="tester",
            instrument="cold-plate",
            num_samples=2,
            wells_per_sample=32,
            dict_samples_to_dilution={"Sample_0": 1, "Sample_1": 11},
            di_files=list(names),
            di_combined=di_combined,
        )


# --------------------------------------------------------------- find_frozen_at_temp


def test_find_frozen_at_temp_returns_none_when_absent(tmp_path):
    di = tmp_path / "DI 07.16.25.dat"
    di.write_text("")
    assert find_frozen_at_temp(di) is None


def test_find_frozen_at_temp_matches_through_reviewed_infix(tmp_path):
    """SpacedTempCSV names its output after the *reviewed* .dat, not the raw one."""
    di = tmp_path / "DI 07.16.25.dat"
    di.write_text("")
    expected = _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI 07.16.25.csv", [[-20.0, 1, 2]])
    assert find_frozen_at_temp(di) == expected


def test_find_frozen_at_temp_picks_latest_version(tmp_path):
    di = tmp_path / "DI 07.16.25.dat"
    di.write_text("")
    _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI 07.16.25.csv", [[-20.0, 1, 2]])
    latest = _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI 07.16.25(1).csv", [[-20.0, 3, 4]])
    assert find_frozen_at_temp(di) == latest


def test_find_frozen_at_temp_ignores_other_di_files(tmp_path):
    """Two DI plates in one folder must not resolve to each other's binned file."""
    di_a = tmp_path / "DI a 07.16.25.dat"
    di_b = tmp_path / "DI b 07.16.25.dat"
    di_a.write_text("")
    di_b.write_text("")
    frozen_a = _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25.csv", [[-20.0, 1, 2]])
    assert find_frozen_at_temp(di_a) == frozen_a
    assert find_frozen_at_temp(di_b) is None


def test_find_frozen_at_temp_ignores_a_longer_stem(tmp_path):
    """`DI a 07.16.25` must not resolve to a file binned for `DI a 07.16.25 rerun`."""
    di = tmp_path / "DI a 07.16.25.dat"
    di.write_text("")
    _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25 rerun.csv", [[-20.0, 1, 2]])
    assert find_frozen_at_temp(di) is None


# ------------------------------------------------------------------------- di_dates


def test_di_dates_single_date(tmp_path):
    assert di_dates([tmp_path / "DI a 07.16.25.dat"]) == "07.16.25"


def test_di_dates_dedupes_shared_date(tmp_path):
    files = [tmp_path / "DI a 07.16.25.dat", tmp_path / "DI b 07.16.25.dat"]
    assert di_dates(files) == "07.16.25"


def test_di_dates_joins_distinct_dates(tmp_path):
    files = [tmp_path / "DI a 07.16.25.dat", tmp_path / "DI b 07.17.25.dat"]
    assert di_dates(files) == "07.16.25_07.17.25"


def test_di_dates_warns_without_a_date(tmp_path):
    with pytest.warns(UserWarning, match="No date found"):
        assert di_dates([tmp_path / "DI plate.dat"]) == "unknown"


# -------------------------------------------------------------------- find_combined


def test_find_combined_returns_none_when_absent(tmp_path):
    assert find_combined(tmp_path, "avg", "07.16.25") is None


def test_find_combined_ignores_a_longer_date_tag(tmp_path):
    """A one-date DI set must not pick up the combined file of a two-date set."""
    combined_path(tmp_path, "avg", "07.16.25_07.17.25").write_text("x")
    assert find_combined(tmp_path, "avg", "07.16.25") is None


def test_find_combined_still_matches_version_suffixes(tmp_path):
    versioned = combined_path(tmp_path, "avg", "07.16.25")
    versioned.with_name("combined_DI_avg_07.16.25(1).csv").write_text("x")
    assert find_combined(tmp_path, "avg", "07.16.25") is not None


def test_find_combined_is_specific_to_method_and_date(tmp_path):
    combined_path(tmp_path, "avg", "07.16.25").write_text("x")
    assert find_combined(tmp_path, "avg", "07.16.25") is not None
    assert find_combined(tmp_path, "sum", "07.16.25") is None
    assert find_combined(tmp_path, "avg", "07.17.25") is None


# ----------------------------------------------------------------------- combine_di


def _read_combined(path):
    """Read back a combined DI file, skipping the metadata header block."""
    with open(path) as f:
        lines = f.readlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("degC,"))
    return pd.read_csv(path, skiprows=start)


@pytest.fixture
def two_di_frozen(tmp_path):
    a = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25.csv", [[-20.0, 4, 2], [-20.5, 9, 5]]
    )
    b = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI b 07.16.25.csv", [[-20.0, 6, 4], [-20.5, 11, 7]]
    )
    return [a, b]


def test_combine_di_avg(tmp_path, two_di_frozen):
    out = combine_di(two_di_frozen, "avg", tmp_path, "07.16.25", 32)
    assert out == combined_path(tmp_path, "avg", "07.16.25")
    df = _read_combined(out)
    assert list(df["degC"]) == [-20.0, -20.5]  # warm to cold, as frozen_at_temp files run
    assert list(df["Sample_0"]) == [5, 10]
    assert list(df["Sample_1"]) == [3, 6]
    assert list(df["di_count"]) == [2, 2]


def test_combine_di_sum(tmp_path, two_di_frozen):
    df = _read_combined(combine_di(two_di_frozen, "sum", tmp_path, "07.16.25", 32))
    assert list(df["Sample_0"]) == [10, 20]
    assert list(df["Sample_1"]) == [6, 12]


def test_combine_di_records_partial_temperature_coverage(tmp_path):
    """A bin only one DI run reached must be visible through di_count, not silent."""
    a = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25.csv", [[-20.0, 4, 2], [-20.5, 9, 5]]
    )
    b = _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI b 07.16.25.csv", [[-20.0, 6, 4]])
    df = _read_combined(combine_di([a, b], "avg", tmp_path, "07.16.25", 32))
    assert list(df["di_count"]) == [2, 1]


def test_di_count_flags_bins_that_were_carried_forward(tmp_path):
    """di_count means "measured here", not "inside this run's span".

    The off-grid first-frozen rows that make alignment necessary sit *inside* both runs'
    spans, so a span test would report full coverage exactly where a value was ffilled —
    leaving the column unable to flag the one thing it exists to flag.
    """
    a = _write_frozen(
        tmp_path,
        "frozen_at_temp_reviewed_DI a 07.16.25.csv",
        [[-4.0, 0, 0], [-4.1, 1, 0], [-4.5, 1, 1], [-5.0, 2, 1]],
    )
    b = _write_frozen(
        tmp_path,
        "frozen_at_temp_reviewed_DI b 07.16.25.csv",
        [[-4.0, 0, 0], [-4.5, 0, 0], [-5.0, 1, 1], [-5.3, 2, 2]],
    )
    df = _read_combined(combine_di([a, b], "avg", tmp_path, "07.16.25", 32))
    counts = dict(zip(df["degC"], df["di_count"], strict=True))
    assert counts[-4.1] == 1  # run b carried forward
    assert counts[-5.3] == 1  # run a carried forward
    assert counts[-4.0] == counts[-4.5] == counts[-5.0] == 2


def test_find_frozen_at_temp_ignores_a_stem_that_only_ends_the_same_way(tmp_path):
    """Two DI files must not resolve to the same binned csv."""
    di = tmp_path / "DI a 07.16.25.dat"
    di.write_text("")
    _write_frozen(tmp_path, "frozen_at_temp_reviewed_second DI a 07.16.25.csv", [[-20.0, 1, 2]])
    assert find_frozen_at_temp(di) is None


def test_combine_di_does_not_reuse_a_file_built_for_another_plate_size(tmp_path, two_di_frozen):
    """di_wells is derived from wells_per_sample, so a different plate makes it stale."""
    combine_di(two_di_frozen, "sum", tmp_path, "07.16.25", 32)
    with pytest.warns(UserWarning, match="wells_per_sample"):
        out = combine_di(two_di_frozen, "sum", tmp_path, "07.16.25", 96)
    assert list(_read_combined(out)["di_wells"]) == [192, 192]


def test_combine_di_writes_provenance_header(tmp_path, two_di_frozen):
    out = combine_di(two_di_frozen, "avg", tmp_path, "07.16.25", 32)
    text = out.read_text()
    assert "di_combined = avg" in text
    assert "di_date = 07.16.25" in text
    assert "frozen_at_temp_reviewed_DI a 07.16.25.csv" in text


def test_combine_di_reuses_existing_combined_file(tmp_path, two_di_frozen):
    """A second run must not recompute or duplicate the combined file."""
    first = combine_di(two_di_frozen, "avg", tmp_path, "07.16.25", 32)
    marker = first.read_text()
    second = combine_di(two_di_frozen, "avg", tmp_path, "07.16.25", 32)
    assert second == first
    assert second.read_text() == marker
    assert len(list(tmp_path.glob("combined_DI_avg_*.csv"))) == 1


def test_combine_di_single_writes_the_same_schema(tmp_path):
    """Every method returns one schema, so callers never branch on di_combined."""
    only = _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI 07.16.25.csv", [[-20.0, 4, 2]])
    out = combine_di([only], "single", tmp_path, "07.16.25", 32)
    assert out == combined_path(tmp_path, "single", "07.16.25")
    df = _read_combined(out)
    assert list(df["Sample_0"]) == [4]
    assert list(df["di_count"]) == [1]
    assert list(df["di_wells"]) == [32]


def test_combine_di_single_rejects_multiple(tmp_path, two_di_frozen):
    with pytest.raises(ValueError, match="exactly one DI file"):
        combine_di(two_di_frozen, "single", tmp_path, "07.16.25", 32)


def test_combine_di_rejects_unknown_method(tmp_path, two_di_frozen):
    with pytest.raises(ValueError, match="Unknown di_combined method"):
        combine_di(two_di_frozen, "median", tmp_path, "07.16.25", 32)


def test_combine_di_rejects_files_without_sample_columns(tmp_path):
    bad = tmp_path / "frozen_at_temp_reviewed_DI 07.16.25.csv"
    pd.DataFrame({"degC": [-20.0], "other": [1]}).to_csv(bad, index=False)
    with pytest.raises(ValueError, match="No Sample_. columns"):
        combine_di([bad, bad], "avg", tmp_path, "07.16.25", 32)


def test_combine_di_stays_monotonic_with_off_grid_first_frozen_rows(tmp_path):
    """SpacedTempCSV writes one off-grid first-frozen row per run, at different places.

    Grouping the raw union would leave those bins fed by a single run while their
    neighbours are fed by all of them, so the spectrum would go *down* as the plate gets
    colder. Frozen wells can only increase as temperature falls.
    """
    a = _write_frozen(
        tmp_path,
        "frozen_at_temp_reviewed_DI a 07.16.25.csv",
        [[-8.0, 0, 0], [-8.3, 1, 0], [-8.5, 1, 1], [-9.0, 2, 1]],
    )
    b = _write_frozen(
        tmp_path,
        "frozen_at_temp_reviewed_DI b 07.16.25.csv",
        [[-8.0, 0, 0], [-8.5, 0, 0], [-9.0, 2, 2], [-9.1, 3, 2]],
    )
    df = _read_combined(combine_di([a, b], "avg", tmp_path, "07.16.25", 32))
    assert list(df["degC"]) == [-8.0, -8.3, -8.5, -9.0, -9.1]
    for col in ("Sample_0", "Sample_1"):
        values = list(df[col])
        assert values == sorted(values), f"{col} is not monotonic: {values}"


def test_combine_di_carries_values_forward_onto_the_shared_axis(tmp_path):
    """A run with no row at a bin still had its last (warmer) count standing."""
    a = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25.csv", [[-20.0, 2, 0], [-20.3, 6, 0]]
    )
    b = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI b 07.16.25.csv", [[-20.0, 4, 0], [-20.5, 8, 0]]
    )
    df = _read_combined(combine_di([a, b], "sum", tmp_path, "07.16.25", 32))
    # at -20.3 run b has no row, so its -20.0 value of 4 carries forward: 6 + 4 = 10
    assert dict(zip(df["degC"], df["Sample_0"], strict=True)) == {-20.0: 6, -20.3: 10, -20.5: 14}


def test_combine_di_avg_rounds_half_up(tmp_path):
    """Two runs one well apart land on .5 constantly; half-to-even would bias alternate bins."""
    a = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25.csv", [[-20.0, 3, 5], [-20.5, 4, 6]]
    )
    b = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI b 07.16.25.csv", [[-20.0, 4, 6], [-20.5, 5, 7]]
    )
    df = _read_combined(combine_di([a, b], "avg", tmp_path, "07.16.25", 32))
    assert list(df["Sample_0"]) == [4, 5]  # 3.5 -> 4, 4.5 -> 5, not numpy's 4 then 4
    assert list(df["Sample_1"]) == [6, 7]  # 5.5 -> 6, 6.5 -> 7, not 6 then 6


def test_combine_di_sum_records_the_pooled_denominator(tmp_path, two_di_frozen):
    """Summed counts need a pooled well total or the background has no denominator."""
    df = _read_combined(combine_di(two_di_frozen, "sum", tmp_path, "07.16.25", 32))
    assert list(df["di_wells"]) == [64, 64]


def test_combine_di_sum_denominator_covers_extrapolated_bins(tmp_path):
    """A bin only one run reached still sums both runs, so both plates are the pool."""
    a = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25.csv", [[-20.0, 2, 0], [-20.5, 4, 0]]
    )
    b = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI b 07.16.25.csv", [[-20.0, 3, 0], [-21.0, 9, 0]]
    )
    df = _read_combined(combine_di([a, b], "sum", tmp_path, "07.16.25", 32))
    assert list(df["di_count"]) == [2, 1, 1]  # -20.5 is run a alone, -21.0 run b alone
    assert list(df["di_wells"]) == [64, 64, 64]
    assert list(df["Sample_0"]) == [5, 7, 13]  # -21.0: run a carries 4 forward, + b's 9


def test_combine_di_avg_keeps_one_plate_denominator(tmp_path, two_di_frozen):
    df = _read_combined(combine_di(two_di_frozen, "avg", tmp_path, "07.16.25", 32))
    assert list(df["di_wells"]) == [32, 32]


def test_combine_di_rejects_mismatched_sample_columns(tmp_path):
    """concat would NaN-fill, and sum would then read a missing column as zero frozen."""
    a = tmp_path / "frozen_at_temp_reviewed_DI a 07.16.25.csv"
    pd.DataFrame([[-20.0, 4, 2]], columns=["degC", "Sample_0", "Sample_1"]).to_csv(a, index=False)
    b = tmp_path / "frozen_at_temp_reviewed_DI b 07.16.25.csv"
    pd.DataFrame([[-20.0, 6]], columns=["degC", "Sample_0"]).to_csv(b, index=False)
    with pytest.raises(ValueError, match="do not share the same Sample"):
        combine_di([a, b], "avg", tmp_path, "07.16.25", 32)


def test_combine_di_does_not_reuse_a_file_built_from_other_inputs(tmp_path, two_di_frozen):
    """The filename carries method and date but not which runs went in."""
    combine_di(two_di_frozen, "avg", tmp_path, "07.16.25", 32)
    rerun = _write_frozen(
        tmp_path, "frozen_at_temp_reviewed_DI a 07.16.25(1).csv", [[-20.0, 9, 9], [-20.5, 9, 9]]
    )
    with pytest.warns(UserWarning, match="was built from"):
        out = combine_di([rerun, two_di_frozen[1]], "avg", tmp_path, "07.16.25", 32)
    assert list(_read_combined(out)["Sample_0"]) == [8, 10]
    assert len(list(tmp_path.glob("combined_DI_avg_*.csv"))) == 2


def test_ensure_frozen_at_temp_destroys_its_review_root(tmp_path, monkeypatch):
    """quit() leaves tkinter._default_root pinned; only destroy() clears it.

    Without this the sample review that follows builds its PhotoImages in the DI's dead
    interpreter and dies with `image "pyimageN" doesn't exist` on its very first photo —
    on the first cold-plate run, which is the only run where the DI GUI opens at all.
    """
    di = tmp_path / "DI 07.16.25.dat"
    di.write_text("")
    events = []

    class _FakeWindow:
        def mainloop(self):
            events.append("mainloop")

        def destroy(self):
            events.append("destroy")

    def _fake_spaced(*args, **kwargs):
        _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI 07.16.25.csv", [[-20.0, 1, 2]])

        class _Fake:
            data_file = tmp_path / "reviewed_DI 07.16.25.dat"

            def create_temp_csv(self, *a, **k):
                return None

        return _Fake()

    monkeypatch.setattr(di_background.tk, "Tk", lambda *a, **k: _FakeWindow())
    monkeypatch.setattr(di_background, "FreezingReviewer", lambda *a, **k: None)
    monkeypatch.setattr(di_background, "SpacedTempCSV", _fake_spaced)

    config = _cold_plate_config(tmp_path, ["DI 07.16.25.dat"])
    di_background.ensure_frozen_at_temp(di, config)
    assert events == ["mainloop", "destroy"]


def test_ensure_frozen_at_temp_reports_a_review_closed_early(tmp_path, monkeypatch):
    """DataHandler returns its FileNotFoundError instead of raising, so guard explicitly."""
    di = tmp_path / "DI 07.16.25.dat"
    di.write_text("")

    class _FakeWindow:
        def mainloop(self):
            return None

        def destroy(self):
            return None

    class _NoData:
        data_file = None

    monkeypatch.setattr(di_background.tk, "Tk", lambda *a, **k: _FakeWindow())
    monkeypatch.setattr(di_background, "FreezingReviewer", lambda *a, **k: None)
    monkeypatch.setattr(di_background, "SpacedTempCSV", lambda *a, **k: _NoData())

    config = _cold_plate_config(tmp_path, ["DI 07.16.25.dat"])
    with pytest.raises(FileNotFoundError, match="closed before the last image"):
        di_background.ensure_frozen_at_temp(di, config)


# -------------------------------------------------------------- resolve_di_background


@pytest.fixture
def no_gui(monkeypatch):
    """Fail loudly if anything tries to open the review GUI."""

    def _boom(*args, **kwargs):
        raise AssertionError("the review GUI must not open when the DI is already binned")

    monkeypatch.setattr("olaf.processing.di_background.tk.Tk", _boom)
    monkeypatch.setattr("olaf.processing.di_background.FreezingReviewer", _boom)


def test_resolve_di_background_single_skips_gui_when_already_binned(tmp_path, no_gui):
    config = _cold_plate_config(tmp_path, ["DI 07.16.25.dat"])
    _write_frozen(tmp_path, "frozen_at_temp_reviewed_DI 07.16.25.csv", [[-20.0, 4, 2]])
    out = resolve_di_background(config)
    assert out == combined_path(tmp_path, "single", "07.16.25")
    assert list(_read_combined(out)["Sample_0"]) == [4]


def test_resolve_di_background_combines_when_already_binned(tmp_path, no_gui, two_di_frozen):
    config = _cold_plate_config(
        tmp_path, ["DI a 07.16.25.dat", "DI b 07.16.25.dat"], di_combined="avg"
    )
    out = resolve_di_background(config)
    assert out == combined_path(tmp_path, "avg", "07.16.25")
    assert list(_read_combined(out)["Sample_0"]) == [5, 10]


def test_resolve_di_background_is_idempotent(tmp_path, no_gui, two_di_frozen):
    """Re-running a cold-plate experiment reuses everything and opens no GUI."""
    config = _cold_plate_config(
        tmp_path, ["DI a 07.16.25.dat", "DI b 07.16.25.dat"], di_combined="sum"
    )
    assert resolve_di_background(config) == resolve_di_background(config)
    assert len(list(tmp_path.glob("combined_DI_sum_*.csv"))) == 1
