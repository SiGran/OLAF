"""
Tests for olaf.utils.path_utils

Functions under test:
    - natural_sort_key(s)
    - find_latest_file(file_paths)
    - save_df_file(clean_df, save_file, header_info, index)
    - is_within_dates(dates, folder_name)
    - sort_files_by_date(file_paths)

Reference: olaf/utils/path_utils.py
"""

from __future__ import annotations

import pytest

# from olaf.utils.path_utils import (
#     find_latest_file,
#     is_within_dates,
#     natural_sort_key,
#     save_df_file,
#     sort_files_by_date,
# )


class TestNaturalSortKey:
    def test_sorts_image_filenames_naturally(self) -> None:
        """
        Given: ['img1.png', 'img10.png', 'img2.png']
        When:  sorted with key=natural_sort_key
        Then:  order is img1, img2, img10 (NOT lexical img1, img10, img2)
        """
        pytest.skip("not implemented")

    def test_real_image_folder_sorted(self, sgp_test_folder) -> None:
        """
        Given: filenames in tests/test_data/SGP 2.21.24 base/dat_Images/
        When:  sorted with natural_sort_key
        Then:  numeric order matches chronological capture order.

        Real data: SGP 2.21.24 base/dat_Images/
        """
        pytest.skip("not implemented")


class TestFindLatestFile:
    def test_no_versions_returns_only_file(self, tmp_path) -> None:
        """Single file with no (N) suffix is returned as-is."""
        pytest.skip("not implemented")

    def test_picks_highest_version_number(self, tmp_path) -> None:
        """
        Given: foo.csv, foo(1).csv, foo(2).csv, foo(10).csv
        When:  find_latest_file
        Then:  foo(10).csv is returned.
        """
        pytest.skip("not implemented")

    def test_multiple_base_names_picks_most_recent_mtime(self, tmp_path) -> None:
        """
        Given: foo(1).csv and bar(2).csv (different base names)
        When:  find_latest_file
        Then:  the most-recently-modified is returned (mtime tiebreak, line 56-57).
        """
        pytest.skip("not implemented")

    def test_empty_list_returns_none(self) -> None:
        """find_latest_file([]) -> None (early return at line 33)."""
        pytest.skip("not implemented")

    def test_real_sgp_folder_picks_correct_file(self, sgp_test_folder) -> None:
        """
        Given: many `frozen_at_temp_test1_reviewed_*(N).csv` files in SGP 2.21.24 base
        When:  find_latest_file
        Then:  returns the highest-numbered (N) version.

        Real data: SGP 2.21.24 base has versions (1)-(31).
        """
        pytest.skip("not implemented")


class TestIsWithinDates:
    def test_in_range(self) -> None:
        """Folder name with date inside given range returns True."""
        pytest.skip("not implemented")

    def test_before_range(self) -> None:
        pytest.skip("not implemented")

    def test_after_range(self) -> None:
        pytest.skip("not implemented")

    def test_no_date_in_folder_name_returns_false(self) -> None:
        """Folder name without an MM.DD.YY pattern -> False (line 90-91)."""
        pytest.skip("not implemented")

    def test_multiple_dates_in_folder_name_returns_false(self) -> None:
        """
        Folder name like 'KCG 05.21.24 07.19.24 blank' has 2 dates -> returns False.

        Real data: capek/KCG 05.21.24 07.19.24 blank/ (this is the actual case).
        """
        pytest.skip("not implemented")

    def test_malformed_date_string_returns_false(self) -> None:
        """ValueError from strptime is caught -> False (line 104-106)."""
        pytest.skip("not implemented")


class TestSortFilesByDate:
    def test_groups_files_by_date(self, capek_project_folder) -> None:
        """
        Given: a list of frozen_at_temp_*.csv files from capek/* subfolders
        When:  sort_files_by_date
        Then:  defaultdict keyed by 'MM.DD.YY' string, values are lists of
               (Path, trailing_int) tuples.

        Real data: capek/KCG ... folders.
        """
        pytest.skip("not implemented")

    def test_files_without_date_in_name_are_skipped(self, tmp_path) -> None:
        """Files whose name doesn't match DATE_PATTERN aren't added to result."""
        pytest.skip("not implemented")

    def test_trailing_version_extracted_correctly(self, tmp_path) -> None:
        """
        File 'foo 02.21.24 base(7).csv' -> tuple (path, 7).
        File 'foo 02.21.24 base.csv' (no number) -> tuple (path, 0).
        """
        pytest.skip("not implemented")


class TestSaveDfFile:
    def test_saves_with_header_dict(self, tmp_path) -> None:
        """Writes 'filename = ...' followed by each header_info key/value, then CSV."""
        pytest.skip("not implemented")

    def test_collision_appends_counter(self, tmp_path) -> None:
        """If save_file exists, writes save_file(1).csv, then save_file(2).csv, ..."""
        pytest.skip("not implemented")
