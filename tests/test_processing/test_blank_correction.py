"""
Tests for olaf.processing.blank_correction

Class under test: BlankCorrector(project_folder, ...)
    Public:
        .average_blanks(save=True)
        .apply_blanks(save=True, only_within_dates=True, show_comp_plot=False)
    Private (tested directly for edge cases):
        ._find_blank_files(multiple_per_day, blank_includes, blank_excludes)
        ._save_combined_blanks(clean_df, header_info)
        ._final_check(df_corrected, df_inps)
        ._extrapolate_blanks(df_blanks, blank_temps, missing_temps, dates, save=True)

Reference: olaf/processing/blank_correction.py
Bugs from review covered here:
    #3  qc_flag = int (class, not 0)               (blank_correction.py:393)
    #4  Pathological chained comparison            (blank_correction.py:402-410)
    #5  prev_temp -= 1 on float temp label         (blank_correction.py:411)
"""

from __future__ import annotations

import pytest

# from olaf.processing.blank_correction import BlankCorrector


class TestFindBlankFiles:
    """Locating blank folders and the latest INPs_L_*.csv within each."""

    def test_finds_blank_folders_in_test_project(self, test_project_folder) -> None:
        """
        Given: test_project_folder containing 'SGP 5.15.24 6.20.24 blanks/'
        When:  BlankCorrector._find_blank_files runs
        Then:  returns a non-empty list of blank file paths; all paths exist;
               filenames contain 'INPs_L'.

        Real data: tests/test_data/test_project/SGP 5.15.24 6.20.24 blanks/
        """
        pytest.skip("not implemented")

    def test_finds_two_blank_folders_in_capek(self, capek_project_folder) -> None:
        """
        Given: capek_project_folder with TWO blank folders
               ('KCG 05.21.24 07.19.24 blank/' and 'KCG 07.10.24 08.06.24 blank/')
        When:  _find_blank_files runs
        Then:  returns blank files from BOTH folders.

        Real data: tests/test_data/capek/
        """
        pytest.skip("not implemented")

    def test_multiple_per_day_flag(self, capek_project_folder) -> None:
        """multiple_per_day=True vs False changes deduplication behavior."""
        pytest.skip("not implemented")


class TestAverageBlanks:
    """Combining multiple blank INPs_L files into one combined_blank_*.csv."""

    def test_capek_combined_blank_golden(
        self,
        capek_project_folder,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Given: capek with two real blank folders.
        When:  BlankCorrector.average_blanks(save=False)
        Then:  returned DataFrame equals
               goldens/test_blank_correction/capek_combined_blank.csv

        Real data: tests/test_data/capek/KCG 05.21.24 07.19.24 blank/ +
                   tests/test_data/capek/KCG 07.10.24 08.06.24 blank/
        Reference: existing combined_blank_2024-05-21_2024-08-06.csv in repo.
        """
        pytest.skip("not implemented")

    def test_zero_and_negative_inps_filtered_out(self, capek_project_folder) -> None:
        """
        Given: a blank file containing INPS_L <= 0 rows.
        When:  average_blanks runs.
        Then:  those rows are excluded from the average; warning emitted.

        Source: blank_correction.py average_blanks zero/negative filter.
        """
        pytest.skip("not implemented")

    def test_header_info_merged_across_files(self, capek_project_folder) -> None:
        """Header in combined output contains start/end dates spanning all sources."""
        pytest.skip("not implemented")


class TestApplyBlanks:
    """Subtracting combined blanks from sample INPs/L with error propagation."""

    def test_capek_blank_corrected_golden(
        self,
        capek_project_folder,
        goldens_root,
        assert_csv_matches_golden,
    ) -> None:
        """
        Given: capek project (already contains combined_blank_*.csv + sample INPs_L).
        When:  apply_blanks(save=False, only_within_dates=True)
        Then:  for the 'KCG 7.09.24 base' sample, blank-corrected output equals
               goldens/test_blank_correction/capek_kcg_7_09_24_base_corrected.csv

        Real data: tests/test_data/capek/KCG 7.09.24 base/
        """
        pytest.skip("not implemented")

    def test_only_within_dates_filters_out_of_range_samples(self, capek_project_folder) -> None:
        """
        Given: only_within_dates=True
        When:  a sample date lies outside the blank's coverage window
        Then:  that sample is skipped (no blank_corrected_*.csv emitted for it).

        Source: blank_correction.py apply_blanks date-window filter.
        """
        pytest.skip("not implemented")

    def test_only_within_dates_false_processes_all(self, capek_project_folder) -> None:
        """only_within_dates=False: all samples processed regardless of blank window."""
        pytest.skip("not implemented")


class TestFinalCheck:
    """Post-correction QC: monotonicity, error-signal substitution, qc_flag column."""

    def test_qc_flag_column_dtype_pins_current_behavior(self, synthetic_inps_csv_factory) -> None:
        """
        BUG #3 anchor.
        Given: any input passed to _final_check
        When:  it sets df_corrected['qc_flag'] = int  (the class, not 0)
        Then:  qc_flag column dtype is 'object' (current bug). After fix it
               should be int64 with default value 0.

        Source: blank_correction.py:393
        """
        # TODO: build synthetic df_corrected & df_inps via synthetic_inps_csv_factory
        # TODO: call _final_check and assert dtype == object (pins bug)
        pytest.skip("not implemented — pins bug #3 current behavior")

    def test_non_monotonic_corrected_inps_triggers_replacement(
        self, synthetic_inps_csv_factory
    ) -> None:
        """
        BUG #4 anchor.
        Given: df_corrected where INPS_L at a colder temp is LESS than at the
               adjacent warmer temp by more than THRESHOLD_ERROR.
        When:  _final_check runs.
        Then:  the offending row's INPS_L should be replaced with ERROR_SIGNAL
               and qc_flag set. Pin current behavior (likely buggy due to the
               chained-comparison bug); the bugfix commit will update the golden.

        Source: blank_correction.py:402-410
        """
        pytest.skip("not implemented — pins bug #4 current behavior")

    def test_prev_temp_decrement_walks_to_invalid_index(self, synthetic_inps_csv_factory) -> None:
        """
        BUG #5 anchor.
        Given: a degC index spaced at 0.5 °C and a non-monotonic point that
               triggers the prev_temp -= 1 branch.
        When:  _final_check runs.
        Then:  currently KeyError or silent no-op due to integer decrement on
               float labels. Pin observed behavior.

        Source: blank_correction.py:411
        """
        pytest.skip("not implemented — pins bug #5 current behavior")


class TestExtrapolateBlanks:
    """Linear extrapolation when sample covers colder temps than blanks."""

    def test_below_range_linear_extrapolation(self, synthetic_inps_csv_factory) -> None:
        """
        Given: blank covers -10..-20 °C, sample needs -22..-25 °C.
        When:  _extrapolate_blanks runs.
        Then:  returned df has rows at -22..-25; INPS_L values follow linear
               extrapolation of last N points.
        """
        pytest.skip("not implemented")

    def test_non_monotonic_last_point_excluded_from_fit(self, synthetic_inps_csv_factory) -> None:
        """If the last blank point breaks monotonicity, it's excluded from the fit."""
        pytest.skip("not implemented")

    def test_no_extrapolation_needed_returns_input_unchanged(
        self, synthetic_inps_csv_factory
    ) -> None:
        """Sample's coldest temp >= blank's coldest -> no work to do."""
        pytest.skip("not implemented")

    def test_extrapolation_writes_artifact_when_save_true(
        self, synthetic_inps_csv_factory, tmp_path
    ) -> None:
        """
        Given: save=True
        When:  _extrapolate_blanks runs
        Then:  an extrap_comb_b_correction_range_*.csv is written. Verify filename
               pattern matches the real artifacts in capek/test_project.

        Real reference: capek/extrap_comb_b_correction_range_*.csv
        """
        pytest.skip("not implemented")
