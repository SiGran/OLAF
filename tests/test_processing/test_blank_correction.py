"""Tests for olaf.processing.blank_correction (Phase 2.c).
Bugs covered (current behavior pinned):
    #3  qc_flag = int (class, not 0)               (blank_correction.py:393)
    #4  Chained comparison (smell, mostly benign)  (blank_correction.py:402-410)
    #5  prev_temp -= 1 walk-back is dead code      (blank_correction.py:411)
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from olaf.CONSTANTS import ERROR_SIGNAL
from olaf.processing.blank_correction import BlankCorrector


def _empty_corrector(project_folder: Path) -> BlankCorrector:
    return BlankCorrector(
        project_folder=project_folder,
        blank_includes=("__nothing__",),
        blank_excludes=(),
        sample_excludes=(),
    )


def _capek_curated(folder: Path) -> bool:
    if not folder.exists():
        return False
    for sub in folder.iterdir():
        if (
            sub.is_dir()
            and "blank" in sub.name.lower()
            and any(p.name.startswith("INPs_L") for p in sub.iterdir() if p.is_file())
        ):
            return True
    return False


class TestFindBlankFiles:
    def test_finds_blank_folders(self, capek_golden_folder: Path) -> None:
        if not _capek_curated(capek_golden_folder):
            pytest.skip("capek goldens not curated (see goldens/inputs/capek/.NEEDED.md)")
        bc = BlankCorrector(
            project_folder=capek_golden_folder,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        assert bc.blank_files
        for p in bc.blank_files:
            assert p.exists()
            assert "INPs_L" in p.name

    def test_finds_files_from_each_blank_subfolder(self, capek_golden_folder: Path) -> None:
        if not _capek_curated(capek_golden_folder):
            pytest.skip("capek goldens not curated")
        subs = [
            d for d in capek_golden_folder.iterdir() if d.is_dir() and "blank" in d.name.lower()
        ]
        if len(subs) < 2:
            pytest.skip("need >= 2 blank subfolders")
        bc = BlankCorrector(
            project_folder=capek_golden_folder,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        parents = {p.parent.name for p in bc.blank_files}
        assert len(parents) >= 2

    def test_multiple_per_day_flag(self, synthetic_blank_folder) -> None:
        project = synthetic_blank_folder(num_blanks=2, num_samples=0)
        for blank_dir in project.iterdir():
            if "blank" not in blank_dir.name:
                continue
            for csv in list(blank_dir.glob("INPs_L_*.csv")):
                dup = csv.with_name(csv.stem + "(1)" + csv.suffix)
                dup.write_bytes(csv.read_bytes())
        bc_single = BlankCorrector(
            project_folder=project,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
            multiple_per_day=False,
        )
        bc_multi = BlankCorrector(
            project_folder=project,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
            multiple_per_day=True,
        )
        assert len(bc_multi.blank_files) >= len(bc_single.blank_files)


class TestAverageBlanks:
    def test_capek_combined_blank_golden(
        self,
        capek_golden_folder: Path,
        goldens_root: Path,
        assert_csv_matches_golden,
    ) -> None:
        if not _capek_curated(capek_golden_folder):
            pytest.skip("capek goldens not curated")
        bc = BlankCorrector(
            project_folder=capek_golden_folder,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        result = bc.average_blanks(save=False).reset_index()
        # BUG: average_blanks returns tuples (e.g. (1,)) in the dilution column
        # instead of scalar values. The golden CSV stores these as strings "(1,)".
        # Normalize both sides to string for comparison until the bug is fixed.
        result["dilution"] = result["dilution"].astype(str)
        assert_csv_matches_golden(
            result,
            goldens_root / "expected" / "test_blank_correction" / "capek_combined_blank.csv",
        )

    def test_zero_and_negative_inps_filtered_out(self, synthetic_blank_folder) -> None:
        df_zeros = pd.DataFrame(
            {
                "degC": [-18.0, -19.0, -20.0, -21.0],
                "dilution": [1, 1, 1, 1],
                "INPS_L": [0.0, -5.0, 10.0, 20.0],
                "lower_CI": [0.0, 0.0, 5.0, 10.0],
                "upper_CI": [0.0, 0.0, 15.0, 30.0],
            }
        )
        project = synthetic_blank_folder(num_blanks=1, num_samples=0, blank_inps_df=df_zeros)
        bc = BlankCorrector(
            project_folder=project,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        result = bc.average_blanks(save=False)
        assert -18.0 not in result.index
        assert -19.0 not in result.index
        assert -20.0 in result.index
        assert -21.0 in result.index

    def test_header_info_merged_across_files(self, synthetic_blank_folder) -> None:
        df = pd.DataFrame(
            {
                "degC": [-20.0, -21.0],
                "dilution": [1, 1],
                "INPS_L": [10.0, 20.0],
                "lower_CI": [5.0, 10.0],
                "upper_CI": [15.0, 30.0],
            }
        )
        project = synthetic_blank_folder(num_blanks=2, num_samples=0, blank_inps_df=df)
        bc = BlankCorrector(
            project_folder=project,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        bc.average_blanks(save=False)
        (key,) = list(bc.combined_blank.keys())
        start, end = key  # type: ignore[misc]  # class annotates str but values are datetimes
        assert start.month == 5  # type: ignore[attr-defined]
        assert end.month == 6  # type: ignore[attr-defined]


class TestApplyBlanks:
    def test_capek_blank_corrected_golden(
        self,
        capek_golden_folder: Path,
        goldens_root: Path,
        assert_csv_matches_golden,
        tmp_path: Path,
    ) -> None:
        if not _capek_curated(capek_golden_folder):
            pytest.skip("capek goldens not curated")
        work = tmp_path / "capek"
        shutil.copytree(capek_golden_folder, work)
        bc = BlankCorrector(
            project_folder=work,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        bc.average_blanks(save=False)
        bc.apply_blanks(save=True, only_within_dates=False, show_comp_plot=False)
        produced = sorted(work.rglob("blank_corrected_*.csv"))
        if not produced:
            pytest.skip("no sample folders curated for apply_blanks")
        from olaf.utils.df_utils import read_with_flexible_header

        _, actual = read_with_flexible_header(
            produced[0],
            expected_columns=("degC", "dilution", "INPS_L", "lower_CI", "upper_CI", "qc_flag"),
        )
        assert_csv_matches_golden(
            actual,
            goldens_root / "expected" / "test_blank_correction" / f"{produced[0].stem}.csv",
        )

    def test_only_within_dates_filters_out_of_range_samples(self, synthetic_blank_folder) -> None:
        df = pd.DataFrame(
            {
                "degC": [-20.0, -21.0, -22.0],
                "dilution": [1, 1, 1],
                "INPS_L": [10.0, 20.0, 40.0],
                "lower_CI": [5.0, 10.0, 20.0],
                "upper_CI": [15.0, 30.0, 60.0],
            }
        )
        project = synthetic_blank_folder(
            num_blanks=1,
            num_samples=1,
            blank_inps_df=df,
            sample_inps_df=df,
            sample_header_overrides=[
                {
                    "start_time": "2024-09-10 00:00:00",
                    "end_time": "2024-09-10 12:00:00",
                }
            ],
        )
        for sub in project.iterdir():
            if "blank" not in sub.name and sub.is_dir():
                sub.rename(sub.parent / "TEST 09.10.24 base")
                break
        bc = BlankCorrector(
            project_folder=project,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        bc.average_blanks(save=False)
        bc.apply_blanks(save=True, only_within_dates=True)
        assert list(project.rglob("blank_corrected_*.csv")) == []

    def test_only_within_dates_false_processes_all(self, synthetic_blank_folder) -> None:
        df = pd.DataFrame(
            {
                "degC": [-20.0, -21.0, -22.0],
                "dilution": [1, 1, 1],
                "INPS_L": [10.0, 20.0, 40.0],
                "lower_CI": [5.0, 10.0, 20.0],
                "upper_CI": [15.0, 30.0, 60.0],
            }
        )
        project = synthetic_blank_folder(
            num_blanks=1,
            num_samples=1,
            blank_inps_df=df,
            sample_inps_df=df,
            sample_header_overrides=[
                {
                    "start_time": "2024-09-10 00:00:00",
                    "end_time": "2024-09-10 12:00:00",
                }
            ],
        )
        for sub in project.iterdir():
            if "blank" not in sub.name and sub.is_dir():
                sub.rename(sub.parent / "TEST 09.10.24 base")
                break
        bc = BlankCorrector(
            project_folder=project,
            blank_includes=("INPs_L",),
            blank_excludes=("blank_corrected",),
            sample_excludes=(),
        )
        bc.average_blanks(save=False)
        bc.apply_blanks(save=True, only_within_dates=False)
        produced = list(project.rglob("blank_corrected_*.csv"))
        assert len(produced) == 1


def _final_check_inputs(inps_l, lower_ci=None, upper_ci=None, corrected=None):
    n = len(inps_l)
    lower = lower_ci if lower_ci is not None else [v * 0.5 for v in inps_l]
    upper = upper_ci if upper_ci is not None else [v * 1.5 for v in inps_l]
    corr = corrected if corrected is not None else list(inps_l)
    degc = [-20.0 - 0.5 * i for i in range(n)]
    df_inps = pd.DataFrame({"degC": degc, "INPS_L": inps_l, "lower_CI": lower, "upper_CI": upper})
    df_corrected = pd.DataFrame(
        {"degC": degc, "INPS_L": corr, "lower_CI": lower, "upper_CI": upper}
    )
    return df_corrected, df_inps


class TestFinalCheck:
    def test_qc_flag_column_dtype_pins_current_behavior(self, tmp_path: Path) -> None:
        """BUG #3: `df_corrected["qc_flag"] = int` assigns the int CLASS to all rows.
        Loop overwrites every row to 0 or 1 but dtype stays 'object'.
        """
        bc = _empty_corrector(tmp_path)
        df_c, df_i = _final_check_inputs([10.0, 20.0, 40.0, 80.0, 160.0])
        result = bc._final_check(df_c, df_i)
        assert result["qc_flag"].dtype == object
        assert set(result["qc_flag"].unique()).issubset({0, 1})

    def test_monotonic_input_yields_all_zero_qc(self, tmp_path: Path) -> None:
        bc = _empty_corrector(tmp_path)
        df_c, df_i = _final_check_inputs([10.0, 20.0, 40.0, 80.0, 160.0])
        result = bc._final_check(df_c, df_i)
        assert (result["qc_flag"] == 0).all()

    def test_non_monotonic_corrected_inps_triggers_replacement(self, tmp_path: Path) -> None:
        """BUG #4: chained comparison fires here; row[2] is replaced with row[1]."""
        bc = _empty_corrector(tmp_path)
        df_c, df_i = _final_check_inputs(
            inps_l=[10.0, 50.0, 30.0, 80.0, 160.0],
            corrected=[10.0, 50.0, 30.0, 80.0, 160.0],
        )
        result = bc._final_check(df_c, df_i)
        assert result.iloc[2]["INPS_L"] == 50.0
        assert result.iloc[2]["qc_flag"] == 1

    def test_prev_temp_decrement_with_error_signal_pins_behavior(self, tmp_path: Path) -> None:
        """BUG #5: when prev row is ERROR_SIGNAL, chained cmp short-circuits and
        the walk-back loop is unreachable. Current row stays untouched.
        """
        bc = _empty_corrector(tmp_path)
        df_c, df_i = _final_check_inputs(
            inps_l=[10.0, 50.0, 50.0, 30.0, 160.0],
            corrected=[10.0, 50.0, ERROR_SIGNAL, 30.0, 160.0],
        )
        result = bc._final_check(df_c, df_i)
        assert result.iloc[2]["INPS_L"] == ERROR_SIGNAL
        assert result.iloc[3]["INPS_L"] == 30.0
        assert result.iloc[3]["qc_flag"] == 0


def _blank_df(temps, inps, lower=None, upper=None):
    n = len(temps)
    return pd.DataFrame(
        {
            # Object dtype with tuple cells matches real combined_blank format —
            # required so _extrapolate_blanks can inject extrapolated rows whose
            # dilution is a tuple from unique_dilutions().
            "dilution": pd.Series([(1,)] * n, dtype=object),
            "INPS_L": inps,
            "lower_CI": lower if lower is not None else [v * 0.5 for v in inps],
            "upper_CI": upper if upper is not None else [v * 1.5 for v in inps],
            "blank_count": [1] * n,
        },
        index=pd.Index(temps, name="degC"),
    ).sort_index(ascending=False)


class TestExtrapolateBlanks:
    def test_below_range_linear_extrapolation(self, tmp_path: Path) -> None:
        bc = _empty_corrector(tmp_path)
        df = _blank_df([-20.0, -21.0, -22.0, -23.0], [10.0, 20.0, 40.0, 80.0])
        bt = df.index.to_series()
        dates = (pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-15"))
        out, _ = bc._extrapolate_blanks(df, bt, {-24.0, -25.0}, dates, save=False)
        assert -24.0 in out.index
        assert -25.0 in out.index
        assert list(out.index) == sorted(out.index, reverse=True)
        assert out.loc[-24.0, "blank_count"] == 0
        assert out.loc[-25.0, "blank_count"] == 0

    def test_non_monotonic_last_point_excluded_from_fit(self, tmp_path: Path) -> None:
        bc = _empty_corrector(tmp_path)
        df = _blank_df([-20.0, -21.0, -22.0, -23.0], [10.0, 20.0, 40.0, 5.0])
        bt = df.index.to_series()
        dates = (pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-15"))
        out, _ = bc._extrapolate_blanks(df, bt, {-24.0}, dates, save=False)
        assert -24.0 in out.index
        assert out.loc[-23.0, "INPS_L"] != 5.0

    def test_no_extrapolation_needed_returns_input_unchanged(self, tmp_path: Path) -> None:
        bc = _empty_corrector(tmp_path)
        df = _blank_df([-20.0, -21.0, -22.0], [10.0, 20.0, 40.0])
        bt = df.index.to_series()
        dates = (pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-15"))
        out, _ = bc._extrapolate_blanks(df, bt, {-15.0, -16.0}, dates, save=False)
        assert set(out.index) == set(df.index)
        for t in df.index:
            assert out.loc[t, "INPS_L"] == df.loc[t, "INPS_L"]

    def test_extrapolation_writes_artifact_when_save_true(self, tmp_path: Path) -> None:
        bc = _empty_corrector(tmp_path)
        df = _blank_df([-20.0, -21.0, -22.0, -23.0], [10.0, 20.0, 40.0, 80.0])
        bt = df.index.to_series()
        dates = (pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-15"))
        bc._extrapolate_blanks(df, bt, {-24.0, -25.0}, dates, save=True)
        artifacts = list(tmp_path.glob("extrap_comb_b_correction_range_*.csv"))
        assert len(artifacts) == 1
        df_read = pd.read_csv(artifacts[0])
        assert len(df_read) == 6
