"""
Tests for olaf.processing.final_file_creation

Class under test: FinalFileCreation(project_folder, includes, excludes)
    Public:
        .create_all_final_files(treatment_dict, header_start)
    Private:
        ._get_files_per_date(includes, excludes)
        ._final_check(df)

Reference: olaf/processing/final_file_creation.py
Bugs from review covered here:
    #10 iloc with label index in _final_check  (final_file_creation.py:205)
"""

from __future__ import annotations

import pytest

# from olaf.processing.final_file_creation import FinalFileCreation


class TestGetFilesPerDate:
    """Grouping blank_corrected_*.csv by sample start_time (from header)."""

    def test_groups_test_project_files_by_date(self, test_project_folder) -> None:
        """
        Given: test_project_folder with multiple treatments on 5.15.24
               (base + heat + peroxide all present).
        When:  _get_files_per_date runs.
        Then:  the 2024-05-15 key maps to a list of >=3 blank_corrected_*.csv paths,
               one per treatment.

        Real data: tests/test_data/test_project/SGP 5.15.24 {base,heat,peroxide}/
        """
        pytest.skip("not implemented")

    def test_excludes_filter_applied(self, test_project_folder) -> None:
        """`excludes` tuple removes folders/files containing any excluded substring."""
        pytest.skip("not implemented")


class TestCreateAllFinalFiles:
    """End-to-end Stage 3 ARM file generation."""

    def test_test_project_final_files_golden(
        self,
        test_project_folder,
        goldens_root,
        assert_csv_matches_golden,
        tmp_path,
    ) -> None:
        """
        Given: test_project with base+heat+peroxide blank_corrected files for 5.15.24.
        When:  create_all_final_files(treatment_dict={...}, header_start={...}).
        Then:  emitted ARM CSV matches goldens/test_final_file_creation/sgp_5_15_24.csv.

        Real reference (already committed): test_project/final_files/SGP_C1_*.csv
        """
        pytest.skip("not implemented")

    def test_capek_final_files_golden(
        self,
        capek_project_folder,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Same as above but for capek's 'KCG 7.09.24' set (base+heat+peroxide all present).

        Real reference: capek/final_files/*.csv
        """
        pytest.skip("not implemented")

    def test_treatment_not_in_dict_emits_warning(self, test_project_folder) -> None:
        """
        Given: a blank_corrected_*.csv whose treatment is not in treatment_dict.
        When:  create_all_final_files runs.
        Then:  warning printed; file is skipped (ERROR_SIGNAL not used as flag).

        Source: final_file_creation.py:84  (currently uses ERROR_SIGNAL as sentinel
        — flagged in review as overload of meanings).
        """
        pytest.skip("not implemented")

    def test_tbs_site_header_adds_altitude_lines(
        self, synthetic_inps_csv_factory, tmp_path
    ) -> None:
        """
        Given: header_start containing site='TBS_X' plus lower/upper altitudes.
        When:  create_all_final_files runs.
        Then:  output header lines include 'lower_altitude' and 'upper_altitude'.
        """
        pytest.skip("not implemented")


class TestFinalCheck:
    """Stripping leading zero rows, NaN/negative -> ERROR_SIGNAL substitution."""

    def test_strips_leading_zero_rows(self, synthetic_inps_csv_factory) -> None:
        """
        BUG #10 anchor.
        Given: a df whose first N rows have all-zero INPS_L across treatments.
        When:  _final_check runs.
        Then:  output starts at the first non-zero row. Pins CURRENT behavior
               using df.iloc[label_idx:] — works because the index is RangeIndex
               here, but the bugfix will switch to .loc and we want the test to
               continue passing identically.

        Source: final_file_creation.py:205
        """
        pytest.skip("not implemented — anchor for bug #10")

    def test_nan_inps_replaced_with_error_signal(self, synthetic_inps_csv_factory) -> None:
        """NaN INPS_L → ERROR_SIGNAL substitution in output."""
        pytest.skip("not implemented")

    def test_negative_inps_replaced_with_error_signal(self, synthetic_inps_csv_factory) -> None:
        """Negative INPS_L → ERROR_SIGNAL substitution."""
        pytest.skip("not implemented")

    def test_lower_ci_below_zero_replaced(self, synthetic_inps_csv_factory) -> None:
        """lower_CI < 0 → ERROR_SIGNAL (CI must be physically meaningful)."""
        pytest.skip("not implemented")
