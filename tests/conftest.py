"""
Shared pytest fixtures and helpers for the OLAF test suite.

================================================================================
REAL TEST DATA INVENTORY (under tests/test_data/)
================================================================================
Each row lists what the folder contains and which test cases it can serve.

  SGP 2.21.24 base/
    - reviewed_*.dat                                   (.dat with "reviewed" prefix)
    - frozen_at_temp_test1_reviewed_*.csv              (Stage 1 intermediate)
    - INPs_L_frozen_at_temp_*.csv                      (Stage 1 final)
    - dat_Images/                                      (microscope images)
    Use for: SpacedTempCSV (air, primary), DataHandler, df_utils,
             FreezingReviewer GUI smoke test.

  SGP 3.28.24 base/
    - frozen_at_temp_reviewed_*.csv (only)
    Use for: secondary SpacedTempCSV golden, path_utils sort tests.

  KCG 09.23.24 base/
    - capek 09.23.24 a base.dat                        (raw .dat)
    - reviewed_*.dat
    - frozen_at_temp_reviewed_*.csv
    - INPs_L_frozen_at_temp_*.csv
    - capek 09.23.24 a base.dat_Images/
    - Main metadata09232024.txt
    Use for: SpacedTempCSV alternative golden, DataLoader image listing.

  capek/                                               (project-style folder)
    - combined_blank_2024-05-21_2024-08-06*.csv        (10 versioned copies)
    - extrap_comb_b_correction_range_*.csv             (extrapolation outputs)
    - final_files/SGP_C1_*.csv                         (3 ARM final files)
    - KCG 06.13.24 base/                               (.dat + reviewed + frozen + INPs_L)
    - KCG 06.19.24 base/, KCG 07.15.24 base/, KCG 07.18.24 base/
    - KCG 7.09.24 base/                                (HAS blank_corrected_*.csv files)
    - KCG 7.09.24 heat/, KCG 7.09.24 peroxide/         (multi-treatment same date)
    - KCG 05.21.24 07.19.24 blank/                     (blank folder)
    - KCG 07.10.24 08.06.24 blank/                     (blank folder)
    Use for: BlankCorrector (find/average/apply/extrapolate),
             FinalFileCreation (multi-treatment), path_utils (find_latest_file),
             FinalFileCreation goldens.

  test_project/                                        (project-style folder)
    - combined_blank_2024-05-15_2024-06-20*.csv
    - extrap_comb_b_correction_range_*.csv
    - extrapolated_blanks.csv
    - final_files/SGP_C1_2024-06-20_*.csv, ...07-20_*.csv (2 ARM finals)
    - SGP 5.15.24 6.20.24 blanks/                      (blank folder)
    - SGP 5.15.24 base/, SGP 5.15.24 heat/, SGP 5.15.24 peroxide/  (multi-treatment)
    - SGP 5.21.24 base/, 6.07.24 base/, 6.14.24 base/, 6.20.24 base redo/
    - SGP 6.02.24 heat/, 6.02.24 peroxide/
    - SGP 7.20.24 heat/, 7.20.24 peroxide/
    - SGP 8.07.24 base/
    Use for: BlankCorrector multi-blank averaging (only_within_dates),
             FinalFileCreation multi-treatment (5.15.24 has all 3 treatments),
             plots.py site/treatment iteration.

================================================================================
FIXTURE CATALOG
================================================================================
Path fixtures (session-scoped):
  test_data_root          -> tests/test_data/
  goldens_root            -> tests/test_data/goldens/
  sgp_test_folder         -> tests/test_data/SGP 2.21.24 base/
  sgp_3_28_folder         -> tests/test_data/SGP 3.28.24 base/
  kcg_test_folder         -> tests/test_data/KCG 09.23.24 base/
  capek_project_folder    -> tests/test_data/capek/
  test_project_folder     -> tests/test_data/test_project/

Dilution dict fixtures (session-scoped):
  sample_dilution_dict_a  -> Side A / IS2 mapping (Sample_0 -> 1, ..., Sample_5 -> inf)
  sample_dilution_dict_b  -> Side B mapping (descending, with float dilutions)
  freezing_point_depression_dict -> {"Sample_0": 2, "Sample_1": 0.2}

Helper fixtures:
  assert_csv_matches_golden(actual_df, golden_path)
      -> asserts pd.testing.assert_frame_equal with rtol=1e-9.
         If env OLAF_REGEN_GOLDEN=1, writes golden_path instead and SKIPS the test.

Synthetic factory fixtures (function-scoped, write into tmp_path):
  synthetic_dat_factory      -> writes a minimal reviewed_*.dat
  synthetic_inps_csv_factory -> writes a minimal INPs_L_*.csv (with header lines)
  synthetic_blank_folder     -> writes a project tree with N blank folders + 1 sample

Markers (registered in pyproject.toml):
  integration   -> uses real data goldens, slower
  gui           -> requires DISPLAY (skipped on headless CI)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_data_root() -> Path:
    """Absolute path to tests/test_data/ regardless of cwd."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def goldens_root(test_data_root: Path) -> Path:
    """Centralized location for committed golden CSVs."""
    return test_data_root / "goldens"


@pytest.fixture(scope="session")
def sgp_test_folder(test_data_root: Path) -> Path:
    return test_data_root / "SGP 2.21.24 base"


@pytest.fixture(scope="session")
def sgp_3_28_folder(test_data_root: Path) -> Path:
    return test_data_root / "SGP 3.28.24 base"


@pytest.fixture(scope="session")
def kcg_test_folder(test_data_root: Path) -> Path:
    return test_data_root / "KCG 09.23.24 base"


@pytest.fixture(scope="session")
def capek_project_folder(test_data_root: Path) -> Path:
    return test_data_root / "capek"


@pytest.fixture(scope="session")
def test_project_folder(test_data_root: Path) -> Path:
    return test_data_root / "test_project"


# ---------------------------------------------------------------------------
# Domain dict fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sample_dilution_dict_a() -> dict:
    """Side A / IS2 dilution mapping used by most real fixtures."""
    return {
        "Sample_0": 1,
        "Sample_1": 11,
        "Sample_2": 121,
        "Sample_3": 1331,
        "Sample_4": 14641,
        "Sample_5": float("inf"),
    }


@pytest.fixture(scope="session")
def sample_dilution_dict_b() -> dict:
    """Side B dilution mapping (descending, with float dilutions)."""
    return {
        "Sample_5": 1.5,
        "Sample_4": 19.5,
        "Sample_3": 253.5,
        "Sample_2": 3295.5,
        "Sample_1": 42841.5,
        "Sample_0": float("inf"),
    }


@pytest.fixture(scope="session")
def freezing_point_depression_dict() -> dict:
    """Standard FPD adjustment used by salt/sea-water cases in main.py."""
    return {"Sample_0": 2, "Sample_1": 0.2}


# ---------------------------------------------------------------------------
# Golden CSV helper
# ---------------------------------------------------------------------------


@pytest.fixture
def assert_csv_matches_golden() -> Callable[[pd.DataFrame, Path], None]:
    """
    Returns a callable: assert_csv_matches_golden(actual_df, golden_path).

    Behavior:
        - If env OLAF_REGEN_GOLDEN is set (any non-empty value):
              writes actual_df to golden_path (creating parents) and calls
              pytest.skip("regenerated golden ...").
        - Otherwise reads golden_path with pd.read_csv and asserts equality
          via pd.testing.assert_frame_equal(rtol=1e-9, check_dtype=False).

    Goldens are stored under tests/test_data/goldens/<test_module>/<case>.csv
    (callers pass the full path).
    """

    def _assert(actual_df: pd.DataFrame, golden_path: Path) -> None:
        if os.environ.get("OLAF_REGEN_GOLDEN"):
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            actual_df.to_csv(golden_path, index=False, lineterminator="\n")
            pytest.skip(f"regenerated golden: {golden_path}")
        if not golden_path.exists():
            pytest.fail(
                f"Missing golden: {golden_path}\n" f"Run with OLAF_REGEN_GOLDEN=1 to create it."
            )
        expected = pd.read_csv(golden_path)
        pd.testing.assert_frame_equal(
            actual_df.reset_index(drop=True),
            expected.reset_index(drop=True),
            rtol=1e-9,
            check_dtype=False,
        )

    return _assert


# ---------------------------------------------------------------------------
# Synthetic factory fixtures (fallback for edge cases not covered by real data)
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_dat_factory(tmp_path: Path) -> Callable[..., Path]:
    """
    Build a minimal `reviewed_<name>.dat` file under tmp_path.

    Signature:
        synthetic_dat_factory(
            name: str,
            num_rows: int = 30,
            num_samples: int = 6,
            start_temp: float = 0.0,
            temp_step: float = -0.1,
            sample_profile: Callable[[int, int], int] | None = None,
        ) -> Path  # returns the *folder* containing the .dat (with date in name)

    The folder is named so DATE_PATTERN regex matches (e.g. "synthetic 01.01.24 base").
    Columns: Date, Time, Avg_Temp, Sample_0..Sample_{n-1}, Picture, changes.
    `sample_profile(row_idx, sample_idx) -> int` controls frozen-well counts;
    default is monotonic ramp.

    TODO: implement once first test that needs it is written.
    """

    def _factory(*args, **kwargs) -> Path:  # noqa: ARG001
        raise NotImplementedError(
            "synthetic_dat_factory not yet implemented; build it when first needed."
        )

    return _factory


@pytest.fixture
def synthetic_inps_csv_factory(tmp_path: Path) -> Callable[..., Path]:
    """
    Build a minimal `INPs_L_*.csv` (with metadata header lines) under tmp_path.

    Signature:
        synthetic_inps_csv_factory(
            name: str,
            df: pd.DataFrame,           # must have columns: degC, dilution, INPS_L,
                                        #                    lower_CI, upper_CI [, qc_flag]
            header: dict,               # site, start_time, end_time, treatment, ...
        ) -> Path

    TODO: implement once first test that needs it is written.
    """

    def _factory(*args, **kwargs) -> Path:  # noqa: ARG001
        raise NotImplementedError("synthetic_inps_csv_factory not yet implemented.")

    return _factory


@pytest.fixture
def synthetic_blank_folder(tmp_path: Path) -> Callable[..., Path]:
    """
    Build a project tree under tmp_path containing N blank folders + 1 sample folder.

    Signature:
        synthetic_blank_folder(
            num_blanks: int = 2,
            num_samples_per_blank: int = 1,
            with_sample_folder: bool = True,
        ) -> Path  # returns project root suitable for BlankCorrector(project_folder=...)

    TODO: implement once TestApplyBlanks edge cases need it.
    """

    def _factory(*args, **kwargs) -> Path:  # noqa: ARG001
        raise NotImplementedError("synthetic_blank_folder not yet implemented.")

    return _factory
