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

from datetime import datetime

import pandas as pd
import pytest

from olaf.utils.path_utils import (
    find_latest_file,
    is_within_dates,
    natural_sort_key,
    save_df_file,
    sort_files_by_date,
)


class TestNaturalSortKey:
    def test_sorts_image_filenames_naturally(self) -> None:
        """
        Given: ['img1.png', 'img10.png', 'img2.png']
        When:  sorted with key=natural_sort_key
        Then:  order is img1, img2, img10 (NOT lexical img1, img10, img2).
        """
        names = ["img1.png", "img10.png", "img2.png"]
        assert sorted(names, key=natural_sort_key) == [
            "img1.png",
            "img2.png",
            "img10.png",
        ]

    def test_mixed_case_handled(self) -> None:
        """Letters are lowercased (case-insensitive sort)."""
        assert sorted(["Img2.png", "img1.png"], key=natural_sort_key) == [
            "img1.png",
            "Img2.png",
        ]

    def test_real_image_folder_sorted(self, sgp_golden_folder) -> None:
        """
        Given: filenames in goldens/inputs/sgp_2_21_24_base/dat_images/
        Then:  Image_2.png comes before Image_10.png.

        Real data: goldens/inputs/sgp_2_21_24_base/dat_images/
        """
        images_dir = sgp_golden_folder / "dat_images"
        if not images_dir.exists():
            pytest.skip(f"Real fixture missing: {images_dir}")
        names = [p.name for p in images_dir.iterdir() if p.suffix == ".png"]
        if "Image_2.png" not in names or "Image_10.png" not in names:
            pytest.skip("Expected sample image filenames not present")
        ordered = sorted(names, key=natural_sort_key)
        assert ordered.index("Image_2.png") < ordered.index("Image_10.png")


class TestFindLatestFile:
    def test_empty_list_returns_none(self) -> None:
        """find_latest_file([]) -> None (early return)."""
        assert find_latest_file([]) is None

    def test_no_versions_returns_only_file(self, tmp_path) -> None:
        """Single file with no (N) suffix is returned as-is."""
        f = tmp_path / "foo.csv"
        f.write_text("a")
        assert find_latest_file([f]) == f

    def test_picks_highest_version_number(self, tmp_path) -> None:
        """foo.csv, foo(1).csv, foo(2).csv, foo(10).csv -> foo(10).csv."""
        files = [
            tmp_path / "foo.csv",
            tmp_path / "foo(1).csv",
            tmp_path / "foo(2).csv",
            tmp_path / "foo(10).csv",
        ]
        for f in files:
            f.write_text("a")
        assert find_latest_file(files) == tmp_path / "foo(10).csv"

    def test_multiple_base_names_picks_most_recent_mtime(self, tmp_path) -> None:
        """Different base names -> most-recently-modified wins."""
        import os
        import time

        foo = tmp_path / "foo(1).csv"
        bar = tmp_path / "bar(2).csv"
        foo.write_text("a")
        time.sleep(0.01)
        bar.write_text("b")
        # Force bar mtime to be more recent
        now = time.time()
        os.utime(foo, (now - 10, now - 10))
        os.utime(bar, (now, now))
        assert find_latest_file([foo, bar]) == bar

    def test_real_sgp_folder_picks_correct_file(self, sgp_test_folder) -> None:
        """
        Given: many frozen_at_temp_test1_reviewed_*(N).csv files in SGP 2.21.24 base.
        Then:  returns the highest-numbered (N) version.
        """
        files = list(
            sgp_test_folder.glob("frozen_at_temp_test1_reviewed_sgp ment 02.21.24 a base(*).csv")
        )
        if len(files) < 2:
            pytest.skip(f"Need at least 2 versioned files in {sgp_test_folder}")
        result = find_latest_file(files)
        assert result is not None
        # Extract version number from the result's filename
        import re

        m = re.search(r"\((\d+)\)\.csv$", result.name)
        assert m is not None
        result_version = int(m.group(1))
        # Should match the max version present
        max_version = max(
            int(re.search(r"\((\d+)\)\.csv$", f.name).group(1))  # type: ignore[union-attr]
            for f in files
        )
        assert result_version == max_version


class TestIsWithinDates:
    DATES = (datetime(2024, 5, 1), datetime(2024, 8, 1))

    def test_in_range(self) -> None:
        """Folder name with date inside given range returns True."""
        assert is_within_dates(self.DATES, "SGP 06.20.24 base") is True

    def test_before_range(self) -> None:
        """Date before earliest returns False."""
        assert is_within_dates(self.DATES, "SGP 01.15.24 base") is False

    def test_after_range(self) -> None:
        """Date after latest returns False."""
        assert is_within_dates(self.DATES, "SGP 09.20.24 base") is False

    def test_inclusive_at_boundary(self) -> None:
        """Boundary dates are inclusive."""
        assert is_within_dates(self.DATES, "SGP 05.01.24 base") is True
        assert is_within_dates(self.DATES, "SGP 08.01.24 base") is True

    def test_no_date_in_folder_name_returns_false(self) -> None:
        """Folder name without MM.DD.YY pattern -> False."""
        assert is_within_dates(self.DATES, "SGP base no date") is False

    def test_multiple_dates_in_folder_name_returns_false(self) -> None:
        """
        Real-world: 'KCG 05.21.24 07.19.24 blank' has 2 dates -> returns False.
        Real data: capek/KCG 05.21.24 07.19.24 blank/
        """
        assert is_within_dates(self.DATES, "KCG 05.21.24 07.19.24 blank") is False

    def test_malformed_date_string_returns_false(self) -> None:
        """
        If DATE_PATTERN matches but strptime fails (e.g. invalid month),
        the except catches it and returns False.
        """
        # 13.45.24 looks like the pattern but is invalid date
        # Note: depends on DATE_PATTERN's strictness; if it doesn't match, also False
        assert is_within_dates(self.DATES, "garbage 13.45.24 oops") is False


class TestSortFilesByDate:
    def test_groups_files_by_date(self, tmp_path) -> None:
        """Files with same date go in the same defaultdict bucket."""
        files = [
            tmp_path / "foo 02.21.24 base.csv",
            tmp_path / "bar 02.21.24 base(1).csv",
            tmp_path / "baz 03.28.24 base.csv",
        ]
        for f in files:
            f.write_text("a")
        result = sort_files_by_date(files)
        assert set(result.keys()) == {"02.21.24", "03.28.24"}
        assert len(result["02.21.24"]) == 2
        assert len(result["03.28.24"]) == 1

    def test_files_without_date_in_name_are_skipped(self, tmp_path) -> None:
        """Files whose name doesn't match DATE_PATTERN aren't added."""
        files = [
            tmp_path / "foo 02.21.24 base.csv",
            tmp_path / "no_date_file.csv",
        ]
        for f in files:
            f.write_text("a")
        result = sort_files_by_date(files)
        assert "02.21.24" in result
        # Only the dated file should be present anywhere
        all_paths = [p for v in result.values() for p, _ in v]
        assert files[0] in all_paths
        assert files[1] not in all_paths

    def test_trailing_version_pins_current_quirk(self, tmp_path) -> None:
        """
        Pins current behavior of sort_files_by_date's trailing-number extraction.
        The function uses re.search(r'(\\d+)\\.csv$', name) which requires digits
        IMMEDIATELY before .csv. The '(N).csv' versioning pattern has ')' before
        '.csv', so versioned files all get number=0.

        Only files like 'foo 02.21.24 base7.csv' (digit fused to .csv) would
        actually extract a number. This is likely unintended; documenting the
        quirk here so any fix is intentional.
        """
        f_paren = tmp_path / "foo 02.21.24 base(7).csv"
        f_plain = tmp_path / "foo 02.21.24 base.csv"
        f_fused = tmp_path / "foo 02.21.24 base7.csv"
        for f in (f_paren, f_plain, f_fused):
            f.write_text("a")
        result = sort_files_by_date([f_paren, f_plain, f_fused])
        numbers = sorted(n for _, n in result["02.21.24"])
        # f_paren -> 0 (no digit before .csv), f_plain -> 0, f_fused -> 7
        assert numbers == [0, 0, 7]

    def test_real_capek_folder_groups_correctly(self, capek_project_folder) -> None:
        """
        Given: real frozen_at_temp_*.csv files from capek/KCG ... folders.
        Then:  groups exist for each date; keys match DATE_PATTERN (which
               accepts single-digit months, e.g. '7.09.24').
        """
        files = list(capek_project_folder.rglob("frozen_at_temp_reviewed_*.csv"))
        if not files:
            pytest.skip(f"No real fixtures under {capek_project_folder}")
        result = sort_files_by_date(files)
        assert len(result) > 0
        # DATE_PATTERN allows 1-2 digit month/day, 2-digit year
        import re

        for key in result.keys():
            assert re.match(r"\d{1,2}\.\d{1,2}\.\d{2}", key), f"bad key: {key}"


class TestSaveDfFile:
    def test_saves_with_header_dict(self, tmp_path) -> None:
        """Writes 'filename = ...' first, then header k=v lines, then CSV."""
        df = pd.DataFrame({"degC": [-5.0, -10.0], "INPS_L": [0.001, 0.01]})
        save_file = tmp_path / "out.csv"
        save_df_file(df, save_file, {"site": "TEST", "treatment": "base"})

        content = save_file.read_text()
        lines = content.splitlines()
        assert lines[0] == "filename = out.csv"
        assert lines[1] == "site = TEST"
        assert lines[2] == "treatment = base"
        assert lines[3] == "degC,INPS_L"

    def test_collision_appends_counter(self, tmp_path) -> None:
        """If save_file exists, writes save_file(1).csv, then save_file(2).csv."""
        df = pd.DataFrame({"a": [1]})
        save_file = tmp_path / "out.csv"
        save_file.write_text("existing")
        save_df_file(df, save_file, {})

        expected = tmp_path / "out(1).csv"
        assert expected.exists()
        # Original is untouched
        assert save_file.read_text() == "existing"

    def test_multiple_collisions_increment_counter(self, tmp_path) -> None:
        """out.csv, out(1).csv both exist -> writes out(2).csv."""
        df = pd.DataFrame({"a": [1]})
        save_file = tmp_path / "out.csv"
        save_file.write_text("a")
        (tmp_path / "out(1).csv").write_text("b")
        save_df_file(df, save_file, {})
        assert (tmp_path / "out(2).csv").exists()

    def test_empty_header_info_just_writes_filename_and_csv(self, tmp_path) -> None:
        """Empty header dict still produces a 'filename = ...' line and CSV body."""
        df = pd.DataFrame({"a": [1, 2]})
        save_file = tmp_path / "out.csv"
        save_df_file(df, save_file, {})
        lines = save_file.read_text().splitlines()
        assert lines[0] == "filename = out.csv"
        assert lines[1] == "a"
        assert lines[2:] == ["1", "2"]
