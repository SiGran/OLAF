"""
Tests for olaf.processing.final_file_creation (Phase 2.d).

Class under test: FinalFileCreation(project_folder, includes, excludes)
    Public:
        .create_all_final_files(treatment_dict, header_start)
    Private:
        ._get_files_per_date(includes, excludes)
        ._final_check(df)

Bugs covered (current behavior pinned):
    #10 _final_check uses df.iloc[label_idx:] where label_idx is the
        Series.idxmax() *label* - works only when the index is a RangeIndex
        starting at 0. Pinned with synthetic RangeIndex inputs.
        (final_file_creation.py:216)

Notes on real-data coverage
---------------------------
Both `tests/test_data/test_project/` and `tests/test_data/capek/`
contain blank_corrected_*.csv files whose column header is the OLD
5-column format (degC, dilution, INPS_L, lower_CI, upper_CI) - they
lack the `qc_flag` column that the current FinalFileCreation code
hard-codes into `expected_columns`. Running the current code against
those folders therefore returns an empty `files_per_date`. The
real-data integration tests below are gated on a blank_corrected file
with qc_flag existing; until a human re-emits those fixtures with
qc_flag (Phase 2.c's fix for bug #3 will do that), they skip cleanly.
All meaningful coverage runs through synthetic fixtures.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import pytest

from olaf.CONSTANTS import ERROR_SIGNAL
from olaf.processing.final_file_creation import FinalFileCreation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_DEFAULT_HEADER = {
    "site": "SGP",
    "start_time": "2024-05-15 00:00:00",
    "end_time": "2024-05-15 12:00:00",
    "filter_color": "white",
    "vol_air_filt": "1000",
    "proportion_filter_used": "1.0",
    "vol_susp": "10",
    "treatment": "base",
    "notes": "TEST_NOTES",
    "user": "pytest",
}


def _write_blank_corrected(
    folder: Path,
    treatment: str,
    df: pd.DataFrame | None = None,
    header: dict | None = None,
    filename: str | None = None,
) -> Path:
    """Write a synthetic blank_corrected_*.csv with the full 6-column schema
    that FinalFileCreation currently expects (degC, dilution, INPS_L,
    lower_CI, upper_CI, qc_flag).
    """
    folder.mkdir(parents=True, exist_ok=True)
    if df is None:
        df = pd.DataFrame(
            {
                "degC": [-18.0, -19.0, -20.0, -21.0, -22.0],
                "dilution": [1.0, 1.0, 1.0, 1.0, 1.0],
                "INPS_L": [10.0, 20.0, 40.0, 80.0, 160.0],
                "lower_CI": [5.0, 10.0, 20.0, 40.0, 80.0],
                "upper_CI": [15.0, 30.0, 60.0, 120.0, 240.0],
                "qc_flag": [0, 0, 0, 0, 0],
            }
        )
    merged_header = {**_DEFAULT_HEADER, "treatment": treatment, **(header or {})}
    name = filename or f"blank_corrected_INPs_L_synthetic_{treatment}.csv"
    out = folder / name
    with open(out, "w") as f:
        f.write(f"filename = {out.name}\n")
        for k, v in merged_header.items():
            f.write(f"{k} = {v}\n")
        df.to_csv(f, index=False, lineterminator="\n")
    return out


def _build_project(
    tmp_path: Path,
    treatments: Iterable[str] = ("base", "heat", "peroxide"),
    site: str = "SGP",
    start_time: str = "2024-05-15 00:00:00",
    end_time: str = "2024-05-15 12:00:00",
    header_overrides: dict | None = None,
) -> Path:
    """Create a synthetic project with one subfolder per treatment, each
    containing a single blank_corrected_*.csv sharing the same start_time
    so they group under one date key."""
    root = tmp_path / "project"
    root.mkdir(exist_ok=True)
    for t in treatments:
        sub = root / f"{site} 5.15.24 {t}"
        hdr = {
            "site": site,
            "start_time": start_time,
            "end_time": end_time,
            **(header_overrides or {}),
        }
        _write_blank_corrected(sub, treatment=t, header=hdr)
    return root


# Default includes/excludes (informed by olaf/main_final_combine.py).
_INCLUDES = ("blank_corrected", "INPs_L")
_EXCLUDES = ("blanks", "10%", ".png")


# ---------------------------------------------------------------------------
# _get_files_per_date
# ---------------------------------------------------------------------------


class TestGetFilesPerDate:
    """Grouping blank_corrected_*.csv by sample start_time (from header)."""

    def test_groups_synthetic_treatments_by_date(self, tmp_path: Path) -> None:
        """Three treatment folders sharing start_time -> one date key with 3 files."""
        root = _build_project(tmp_path, treatments=("base", "heat", "peroxide"))
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)

        assert len(ffc.files_per_date) == 1
        ((date_key, files),) = ffc.files_per_date.items()
        assert date_key == "2024-05-15 00:00:00"
        assert len(files) == 3
        treatments_in_filenames = {f.stem.rsplit("_", 1)[-1] for f in files}
        assert treatments_in_filenames == {"base", "heat", "peroxide"}

    def test_different_start_times_yield_separate_keys(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        root.mkdir()
        _write_blank_corrected(
            root / "SGP 5.15.24 base",
            treatment="base",
            header={"start_time": "2024-05-15 00:00:00"},
        )
        _write_blank_corrected(
            root / "SGP 5.16.24 base",
            treatment="base",
            header={"start_time": "2024-05-16 00:00:00"},
            filename="blank_corrected_INPs_L_synthetic_base2.csv",
        )
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        assert set(ffc.files_per_date.keys()) == {
            "2024-05-15 00:00:00",
            "2024-05-16 00:00:00",
        }

    def test_excludes_filter_removes_folder(self, tmp_path: Path) -> None:
        """Folders whose name contains an excluded substring are skipped."""
        root = _build_project(tmp_path, treatments=("base",))
        _write_blank_corrected(
            root / "SGP 5.15.24 6.20.24 blanks",
            treatment="blank",
            header={"start_time": "2024-05-15 00:00:00"},
            filename="blank_corrected_INPs_L_should_be_excluded.csv",
        )
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        all_files = [p for files in ffc.files_per_date.values() for p in files]
        assert all("blanks" not in p.parent.name for p in all_files)


# ---------------------------------------------------------------------------
# create_all_final_files (end-to-end)
# ---------------------------------------------------------------------------


def _read_arm_output(path: Path) -> tuple[list[str], pd.DataFrame]:
    """Split an emitted ARM CSV into (header_lines, body_dataframe).
    Body data rows begin two lines after the 'Temperature (degC)' column
    header line (skipping the UTC-seconds metadata line).
    """
    lines = path.read_text().splitlines()
    body_start = None
    for i, line in enumerate(lines):
        if line.startswith("Temperature (degC)"):
            body_start = i + 2
            break
    assert body_start is not None, f"could not find Temperature row in {path}"
    header_lines = lines[:body_start]
    body_df = pd.read_csv(
        path,
        skiprows=body_start,
        header=None,
        names=[
            "Temperature (degC)",
            "n_INP_STP (per L)",
            "lower_CL (per L)",
            "upper_CL (per L)",
            "QC_flag",
            "Treatment_flag",
        ],
    )
    return header_lines, body_df


class TestCreateAllFinalFiles:
    """End-to-end Stage 3 ARM file generation against a synthetic project."""

    def test_emits_one_arm_file_per_date(self, tmp_path: Path) -> None:
        root = _build_project(tmp_path, treatments=("base", "heat", "peroxide"))
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0, "heat": 1, "peroxide": 2},
            header_start="TEST_HEADER\n",
        )
        final_dir = root / "final_files"
        emitted = list(final_dir.glob("*.csv"))
        assert len(emitted) == 1
        # Filename pattern: <site>_<YYYY-MM-DD>_<HHMMSS>.csv
        assert emitted[0].name == "SGP_2024-05-15_000000.csv"

    def test_arm_body_has_all_treatments_with_correct_flags(self, tmp_path: Path) -> None:
        root = _build_project(tmp_path, treatments=("base", "heat", "peroxide"))
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0, "heat": 1, "peroxide": 2},
            header_start="TEST_HEADER\n",
        )
        (emitted,) = (root / "final_files").glob("*.csv")
        _, body = _read_arm_output(emitted)
        # 5 rows per treatment x 3 treatments.
        assert len(body) == 15
        assert set(body["Treatment_flag"].unique()) == {0, 1, 2}
        # Spot-check confidence-limit math (CI in source -> CL in output)
        first_base = body[body["Treatment_flag"] == 0].iloc[0]
        # INPS_L=10, lower_CI=5  -> lower_CL = 10 - 5 = 5
        # INPS_L=10, upper_CI=15 -> upper_CL = 10 + 15 = 25
        assert first_base["n_INP_STP (per L)"] == pytest.approx(10.0)
        assert first_base["lower_CL (per L)"] == pytest.approx(5.0)
        assert first_base["upper_CL (per L)"] == pytest.approx(25.0)

    def test_header_contains_site_and_filter_color(self, tmp_path: Path) -> None:
        root = _build_project(tmp_path, treatments=("base",))
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0},
            header_start="FIRST_LINE\n",
        )
        (emitted,) = (root / "final_files").glob("*.csv")
        header_text = emitted.read_text()
        assert "FIRST_LINE" in header_text
        assert "Site: SGP" in header_text
        assert "Filter color: white" in header_text
        assert "Sample notes: TEST_NOTES" in header_text
        # Non-TBS branch: no altitude columns
        assert "lower altitude" not in header_text.lower()
        assert "Start (UTC); Stop (UTC); Total_vol (L)" in header_text

    def test_tbs_site_header_adds_altitude_lines(self, tmp_path: Path) -> None:
        """site containing 'TBS' adds altitude columns and altitude metadata."""
        root = tmp_path / "project"
        root.mkdir()
        _write_blank_corrected(
            root / "TBS_X 5.15.24 base",
            treatment="base",
            header={
                "site": "TBS_X",
                "start_time": "2024-05-15 00:00:00",
                "end_time": "2024-05-15 12:00:00",
                "lower_altitude": "100",
                "upper_altitude": "500",
            },
        )
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0},
            header_start="TBS_HEADER\n",
        )
        (emitted,) = (root / "final_files").glob("*.csv")
        text = emitted.read_text()
        assert "Lower altitude range" in text
        assert "Upper altitude range" in text
        # The metadata line should include both altitudes
        assert ",100,500," in text

    def test_treatment_not_in_dict_is_skipped(self, tmp_path: Path) -> None:
        """A blank_corrected file whose treatment isn't in treatment_dict is
        dropped from the body, but the file is still emitted (with the other
        treatments only)."""
        root = _build_project(tmp_path, treatments=("base", "heat"))
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0},  # heat intentionally missing
            header_start="HDR\n",
        )
        (emitted,) = (root / "final_files").glob("*.csv")
        _, body = _read_arm_output(emitted)
        assert set(body["Treatment_flag"].unique()) == {0}
        assert len(body) == 5  # only the base rows survived

    def test_empty_project_creates_no_files(self, tmp_path: Path) -> None:
        root = tmp_path / "empty"
        root.mkdir()
        ffc = FinalFileCreation(root, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0},
            header_start="HDR\n",
        )
        final_dir = root / "final_files"
        if final_dir.exists():
            assert list(final_dir.iterdir()) == []


# ---------------------------------------------------------------------------
# _final_check (unit-level)
# ---------------------------------------------------------------------------


def _final_check_df(inps_l, lower_cl=None, upper_cl=None, treatment_flag=0) -> pd.DataFrame:
    """Build a df with the ARM-renamed columns that _final_check expects."""
    n = len(inps_l)
    lower = lower_cl if lower_cl is not None else [v * 0.5 if v >= 0 else v for v in inps_l]
    upper = upper_cl if upper_cl is not None else [v * 1.5 if v >= 0 else v for v in inps_l]
    return pd.DataFrame(
        {
            "Temperature (degC)": [-18.0 - 0.5 * i for i in range(n)],
            "n_INP_STP (per L)": inps_l,
            "lower_CL (per L)": lower,
            "upper_CL (per L)": upper,
            "QC_flag": [0] * n,
            "Treatment_flag": [treatment_flag] * n,
        }
    )


def _ffc(tmp_path: Path) -> FinalFileCreation:
    root = tmp_path / "empty"
    root.mkdir(exist_ok=True)
    return FinalFileCreation(root, _INCLUDES, _EXCLUDES)


class TestFinalCheck:
    """Stripping leading zero rows, NaN/negative -> ERROR_SIGNAL substitution."""

    def test_strips_leading_zero_rows(self, tmp_path: Path) -> None:
        """BUG #10 anchor.
        Given: a df whose first N rows have all-zero INPS_L.
        When:  _final_check runs.
        Then:  output starts at the first non-zero row.

        Pins CURRENT behavior of df.iloc[first_non_zero_idx:] where
        first_non_zero_idx is a *label* from idxmax() - works here only
        because the input has a RangeIndex starting at 0 (so label == position).
        """
        ffc = _ffc(tmp_path)
        df = _final_check_df([0.0, 0.0, 0.0, 10.0, 20.0])
        result = ffc._final_check(df)
        assert len(result) == 2
        assert result["n_INP_STP (per L)"].tolist() == [10.0, 20.0]

    def test_keeps_all_rows_when_first_is_nonzero(self, tmp_path: Path) -> None:
        ffc = _ffc(tmp_path)
        df = _final_check_df([10.0, 20.0, 40.0])
        result = ffc._final_check(df)
        assert len(result) == 3

    def test_nan_inps_replaced_with_error_signal(self, tmp_path: Path) -> None:
        ffc = _ffc(tmp_path)
        df = _final_check_df([10.0, np.nan, 40.0])
        result = ffc._final_check(df)
        assert result["n_INP_STP (per L)"].iloc[1] == ERROR_SIGNAL

    def test_negative_inps_replaced_with_error_signal(self, tmp_path: Path) -> None:
        ffc = _ffc(tmp_path)
        df = _final_check_df(
            inps_l=[10.0, -5.0, 40.0],
            lower_cl=[5.0, 1.0, 20.0],  # keep lower_CL non-negative so we
            upper_cl=[15.0, 10.0, 60.0],  # isolate the negative-INP branch
        )
        result = ffc._final_check(df)
        assert result["n_INP_STP (per L)"].iloc[1] == ERROR_SIGNAL
        # Other rows untouched
        assert result["n_INP_STP (per L)"].iloc[0] == 10.0
        assert result["n_INP_STP (per L)"].iloc[2] == 40.0

    def test_lower_cl_below_zero_replaced(self, tmp_path: Path) -> None:
        ffc = _ffc(tmp_path)
        df = _final_check_df(
            inps_l=[10.0, 20.0, 40.0],
            lower_cl=[-1.0, 10.0, 20.0],
            upper_cl=[15.0, 30.0, 60.0],
        )
        result = ffc._final_check(df)
        assert result["lower_CL (per L)"].iloc[0] == ERROR_SIGNAL
        assert result["lower_CL (per L)"].iloc[1] == 10.0
        assert result["lower_CL (per L)"].iloc[2] == 20.0

    def test_nan_in_lower_and_upper_cl_replaced(self, tmp_path: Path) -> None:
        ffc = _ffc(tmp_path)
        df = _final_check_df(
            inps_l=[10.0, 20.0],
            lower_cl=[np.nan, 10.0],
            upper_cl=[15.0, np.nan],
        )
        result = ffc._final_check(df)
        assert result["lower_CL (per L)"].iloc[0] == ERROR_SIGNAL
        assert result["upper_CL (per L)"].iloc[1] == ERROR_SIGNAL


# ---------------------------------------------------------------------------
# Real-data integration (skip cleanly when fixtures don't match current schema)
# ---------------------------------------------------------------------------


def _has_blank_corrected_with_qc(folder: Path) -> bool:
    """Whether any blank_corrected_*.csv in `folder` has the 6-column header
    (degC,dilution,INPS_L,lower_CI,upper_CI,qc_flag) the current code needs.
    """
    if not folder.exists():
        return False
    for p in folder.rglob("blank_corrected_*.csv"):
        try:
            with open(p, "r") as f:
                for _ in range(25):
                    line = f.readline()
                    if not line:
                        break
                    if line.startswith("degC,"):
                        if "qc_flag" in line:
                            return True
                        break
        except OSError:
            continue
    return False


class TestRealProjectIntegration:
    """Goldens against committed real-data outputs. Skipped while the
    committed blank_corrected_*.csv fixtures use the legacy 5-column schema
    (no qc_flag) - see module docstring."""

    def test_test_project_final_files_golden(
        self,
        test_project_folder: Path,
        goldens_root: Path,
        assert_csv_matches_golden,
        tmp_path: Path,
    ) -> None:
        if not _has_blank_corrected_with_qc(test_project_folder):
            pytest.skip(
                "test_project blank_corrected_*.csv use legacy 5-col schema "
                "(no qc_flag); regenerate after Phase 3 bugfix #3."
            )
        work = tmp_path / "test_project"
        shutil.copytree(test_project_folder, work)
        ffc = FinalFileCreation(work, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0, "heat": 1, "peroxide": 2},
            header_start="ARM_HEADER\n",
        )
        emitted = sorted((work / "final_files").glob("*.csv"))
        assert emitted, "no final files emitted"
        _, body = _read_arm_output(emitted[0])
        assert_csv_matches_golden(
            body,
            goldens_root / "expected" / "test_final_file_creation" / f"{emitted[0].stem}.csv",
        )

    def test_capek_final_files_golden(
        self,
        capek_project_folder: Path,
        goldens_root: Path,
        assert_csv_matches_golden,
        tmp_path: Path,
    ) -> None:
        if not _has_blank_corrected_with_qc(capek_project_folder):
            pytest.skip(
                "capek blank_corrected_*.csv use legacy 5-col schema "
                "(no qc_flag); regenerate after Phase 3 bugfix #3."
            )
        work = tmp_path / "capek"
        shutil.copytree(capek_project_folder, work)
        ffc = FinalFileCreation(work, _INCLUDES, _EXCLUDES)
        ffc.create_all_final_files(
            treatment_dict={"base": 0, "heat": 1, "peroxide": 2},
            header_start="ARM_HEADER\n",
        )
        emitted = sorted((work / "final_files").glob("*.csv"))
        assert emitted
        _, body = _read_arm_output(emitted[0])
        assert_csv_matches_golden(
            body,
            goldens_root / "expected" / "test_final_file_creation" / f"capek_{emitted[0].stem}.csv",
        )
