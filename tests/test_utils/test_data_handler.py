"""
Tests for olaf.utils.data_handler

Class under test:
    - DataHandler(folder_path, num_samples, **kwargs)
        .get_data_file(includes, excludes, suffix, date_col, sep)
        .save_to_new_file(save_data, save_path, prefix, sep, header)

Reference: olaf/utils/data_handler.py
"""

from __future__ import annotations

import pytest

# from olaf.utils.data_handler import DataHandler


class TestGetDataFile:
    def test_single_match_returns_file_and_df(self, kcg_test_folder) -> None:
        """
        Given: KCG 09.23.24 base/ which contains exactly one 'reviewed_*.dat'
        When:  DataHandler(folder, num_samples=6, includes=("reviewed",), suffix=".dat")
        Then:  data_file is the path, data is a non-empty DataFrame with Date/Time
               columns split correctly.

        Real data: KCG 09.23.24 base/reviewed_capek 09.23.24 a base.dat
        """
        pytest.skip("not implemented")

    def test_multiple_matches_picks_latest_version(self, sgp_test_folder) -> None:
        """
        Given: SGP 2.21.24 base has many 'frozen_at_temp_test1_reviewed_*(N).csv'
        When:  DataHandler(...) with includes matching all of them
        Then:  data_file is the highest (N) version (delegates to find_latest_file).

        Real data: SGP 2.21.24 base/ has versions (1) through (31).
        """
        pytest.skip("not implemented")

    def test_no_match_current_behavior(self, tmp_path) -> None:
        """
        Given: an empty folder
        When:  DataHandler(folder, includes=("nope",))
        Then:  Pins CURRENT behavior: returns (None, FileNotFoundError(...)) tuple
               via get_data_file (line 67-75) -- self.data is the exception object.

        BUG ANCHOR: This is bug #9 from the review. The bugfix will change this
        to `raise FileNotFoundError`. Update this test to assert raises in the
        bugfix commit.
        """
        pytest.skip("not implemented")

    def test_excludes_filters_out_files(self, sgp_test_folder) -> None:
        """
        Given: SGP folder with both 'frozen_at_temp_*' and 'INPs_L_frozen_at_temp_*'
        When:  includes=('frozen_at_temp',), excludes=('INPs_L',)
        Then:  picks frozen_at_temp file, not the INPs_L one.
        """
        pytest.skip("not implemented")

    def test_dat_file_splits_time_into_date_and_time(self, kcg_test_folder) -> None:
        """
        Given: a .dat file (uses default date_col='Time' branch)
        When:  loaded
        Then:  'Time' column is renamed to 'Date', 'Unnamed: 1' to 'Time',
               and a 'changes' column of [0]*num_samples lists is added (line 86-90).
        """
        pytest.skip("not implemented")


class TestSaveToNewFile:
    def test_writes_with_string_header(self, sgp_test_folder, tmp_path) -> None:
        """
        Given: a DataHandler with data loaded
        When:  save_to_new_file(prefix='test', header='site = SGP\\nstart_time = ...')
        Then:  file written with header, then CSV data; returns the new Path.
        """
        pytest.skip("not implemented")

    def test_writes_with_dict_header(self, sgp_test_folder, tmp_path) -> None:
        """Header dict is written as 'key = value' lines (line 154-157)."""
        pytest.skip("not implemented")

    def test_collision_appends_counter(self, sgp_test_folder, tmp_path) -> None:
        """
        Given: target path already exists
        When:  save_to_new_file is called
        Then:  writes file with '(1)', '(2)', ... suffix until unique (line 142-146).
        """
        pytest.skip("not implemented")

    def test_raises_when_no_data_and_no_self_data(self) -> None:
        """save_to_new_file(save_data=None) on instance with no .data raises ValueError."""
        pytest.skip("not implemented")

    def test_raises_when_save_path_not_path(self, sgp_test_folder) -> None:
        """save_to_new_file(save_path='not a path') raises TypeError."""
        pytest.skip("not implemented")
