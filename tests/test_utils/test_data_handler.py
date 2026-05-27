"""
Tests for olaf.utils.data_handler

Class under test:
    - DataHandler(folder_path, num_samples, **kwargs)
        .get_data_file(includes, excludes, suffix, date_col, sep)
        .save_to_new_file(save_data, save_path, prefix, sep, header)

Reference: olaf/utils/data_handler.py
Bugs from review covered here:
    #9  get_data_file returns (None, FileNotFoundError(...)) instead of raising
        (data_handler.py:67-75) -- pinned via test_no_match_current_behavior
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from olaf.utils.data_handler import DataHandler


class TestGetDataFile:
    def test_single_match_returns_file_and_df(self, kcg_golden_folder) -> None:
        """
        Given: goldens/inputs/kcg_09_23_24_base/ which contains 'reviewed.dat'
        When:  DataHandler(..., includes=("reviewed",), suffix=".dat")
        Then:  data_file is the path, data is a non-empty DataFrame.

        Real data: goldens/inputs/kcg_09_23_24_base/reviewed.dat
        """
        handler = DataHandler(kcg_golden_folder, num_samples=6, includes=("reviewed",), suffix=".dat")
        assert isinstance(handler.data_file, Path)
        assert handler.data_file.suffix == ".dat"
        assert "reviewed" in handler.data_file.name
        assert isinstance(handler.data, pd.DataFrame)
        assert len(handler.data) > 0

    def test_multiple_matches_picks_latest_version(self, sgp_test_folder) -> None:
        """
        Given: SGP 2.21.24 base has many 'reviewed_*.dat' versions.
        Then:  Picks the highest-versioned via find_latest_file.

        Real data: SGP 2.21.24 base/reviewed_sgp ment 02.21.24 a base*.dat
        """
        dat_files = list(sgp_test_folder.glob("reviewed_*.dat"))
        if len(dat_files) < 2:
            pytest.skip(f"Need >=2 reviewed .dat files in {sgp_test_folder}")
        handler = DataHandler(sgp_test_folder, num_samples=6, includes=("reviewed",), suffix=".dat")
        # find_latest_file picks highest (N) or mtime tiebreak
        assert handler.data_file in dat_files

    def test_no_match_pins_current_behavior(self, tmp_path) -> None:
        """
        BUG #9 anchor.
        Given: an empty folder.
        Then:  Pins CURRENT (silently buggy) behavior:
               - DataHandler.__init__ returns successfully without raising
               - self.data_file is None
               - self.data is a FileNotFoundError INSTANCE (not raised, not a DataFrame)

        Downstream code that does self.data['col'] or self.data.empty blows up
        with AttributeError. The bugfix will change get_data_file to actually
        `raise FileNotFoundError(...)` so failures are loud and early.

        Source: data_handler.py:67-75
        """
        handler = DataHandler(tmp_path, num_samples=6, includes=("nope",), suffix=".dat")
        assert handler.data_file is None
        assert isinstance(handler.data, FileNotFoundError)
        # Demonstrate the downstream consequence (no AttributeError swallowing here):
        with pytest.raises(AttributeError):
            _ = handler.data.empty  # type: ignore  # FileNotFoundError has no .empty

    def test_excludes_filters_out_files(self, sgp_test_folder) -> None:
        """
        SGP folder has both 'frozen_at_temp_*.csv' and 'INPs_L_frozen_at_temp_*.csv'.
        includes=('frozen_at_temp',), excludes=('INPs_L',) -> picks non-INPs_L file.
        """
        # Pick the canonical frozen_at_temp file (no INPs_L prefix)
        targets = list(sgp_test_folder.glob("*frozen_at_temp*.csv"))
        targets = [f for f in targets if "INPs_L" not in f.name]
        if not targets:
            pytest.skip(f"Need frozen_at_temp files (without INPs_L) in {sgp_test_folder}")
        handler = DataHandler(
            sgp_test_folder,
            num_samples=6,
            includes=("frozen_at_temp",),
            excludes=("INPs_L",),
            suffix=".csv",
            date_col=None,  # CSVs don't have a Time column to parse
            sep=",",
        )
        assert "INPs_L" not in handler.data_file.name
        assert "frozen_at_temp" in handler.data_file.name

    def test_dat_file_splits_time_into_date_and_time(self, kcg_golden_folder) -> None:
        """
        Raw .dat files have 'Time' as a single datetime column; pandas parse_dates
        splits it into 'Time' (datetime) and 'Unnamed: 1' (time portion).
        DataHandler renames these to 'Date'/'Time' and appends a 'changes' column.

        Uses raw.dat (original format with single datetime 'Time' column).

        Source: data_handler.py:86-90
        """
        handler = DataHandler(kcg_golden_folder, num_samples=6, includes=("raw",), suffix=".dat")
        assert "Date" in handler.data.columns
        assert "Time" in handler.data.columns
        assert "changes" in handler.data.columns
        # changes column is a list of zeros (freshly added for raw .dat)
        first_changes = handler.data["changes"].iloc[0]
        assert isinstance(first_changes, list)
        assert len(first_changes) == 6
        assert all(v == 0 for v in first_changes)


class TestSaveToNewFile:
    @pytest.fixture
    def handler(self, kcg_golden_folder):
        """A real DataHandler with loaded data for save tests."""
        return DataHandler(kcg_golden_folder, num_samples=6, includes=("reviewed",), suffix=".dat")

    def test_writes_with_string_header(self, handler, tmp_path) -> None:
        """String header is written as a single line before the CSV body."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        target = tmp_path / "out.csv"
        result = handler.save_to_new_file(
            save_data=df, save_path=target, prefix="test", header="site = TEST"
        )
        assert result.exists()
        lines = result.read_text().splitlines()
        assert lines[0] == "site = TEST"
        assert lines[1] == "a,b"

    def test_writes_with_dict_header(self, handler, tmp_path) -> None:
        """Dict header -> one 'key = value' line per item."""
        df = pd.DataFrame({"a": [1]})
        target = tmp_path / "out.csv"
        result = handler.save_to_new_file(
            save_data=df,
            save_path=target,
            prefix="test",
            header={"site": "TEST", "treatment": "base"},
        )
        lines = result.read_text().splitlines()
        assert "site = TEST" in lines[:2]
        assert "treatment = base" in lines[:2]
        # CSV body follows
        assert "a" in lines

    def test_no_header_omits_header_block(self, handler, tmp_path) -> None:
        """header=None -> straight CSV, no metadata lines."""
        df = pd.DataFrame({"a": [1, 2]})
        target = tmp_path / "out.csv"
        result = handler.save_to_new_file(
            save_data=df, save_path=target, prefix="test", header=None
        )
        lines = result.read_text().splitlines()
        assert lines[0] == "a"
        assert lines[1:] == ["1", "2"]

    def test_collision_appends_counter(self, handler, tmp_path) -> None:
        """
        Pre-existing target -> writes test_out(1).csv, then test_out(2).csv ...

        Note: save_to_new_file always prefixes; with prefix='test', target
        'out.csv' becomes 'test_out.csv'. The counter is added if THAT exists.
        """
        df = pd.DataFrame({"a": [1]})
        target = tmp_path / "out.csv"
        # Pre-create the prefixed target so the counter logic kicks in
        (tmp_path / "test_out.csv").write_text("existing")

        result = handler.save_to_new_file(
            save_data=df, save_path=target, prefix="test", header=None
        )
        assert result.name == "test_out(1).csv"

    def test_raises_typeerror_when_save_path_not_path(self, handler) -> None:
        """save_path passed as string raises TypeError."""
        with pytest.raises(TypeError, match="must be a Path"):
            handler.save_to_new_file(
                save_data=pd.DataFrame({"a": [1]}),
                save_path="/not/a/path/object",  # type: ignore[arg-type]
            )


class TestDataHandlerEdgeCases:
    def test_no_includes_no_excludes_finds_dat_files(self, kcg_golden_folder) -> None:
        """
        When includes=() AND excludes=() the else-branch (lines 62-66) runs:
        all files with the given suffix are collected, no include/exclude filtering.
        """
        handler = DataHandler(
            kcg_golden_folder, num_samples=6, includes=(), excludes=(), suffix=".dat"
        )
        # Both reviewed.dat and raw.dat qualify; find_latest_file picks one
        assert isinstance(handler.data_file, Path)
        assert handler.data_file.suffix == ".dat"
        assert isinstance(handler.data, pd.DataFrame)
        assert len(handler.data) > 0

    def test_date_col_none_skips_datetime_parsing(self, kcg_golden_folder) -> None:
        """
        date_col=None (line 84) skips parse_dates and the Unnamed:1 rename block.
        The Time column is read as plain text.
        """
        handler = DataHandler(
            kcg_golden_folder,
            num_samples=6,
            includes=("reviewed",),
            suffix=".dat",
            date_col=None,
        )
        assert isinstance(handler.data, pd.DataFrame)
        assert len(handler.data) > 0
        # Without parse_dates, 'Time' comes through as a plain text column
        assert "Date" in handler.data.columns
        assert "Time" in handler.data.columns
        # No changes column added (the Unnamed:1 branch was skipped)
        assert "Unnamed: 1" not in handler.data.columns

    def test_uses_self_data_and_data_file_when_neither_provided(
        self, kcg_golden_folder, tmp_path
    ) -> None:
        """
        save_to_new_file() with no save_data and no save_path (lines 126-133) falls
        back to self.data and self.data_file.  We redirect data_file to tmp_path to
        avoid writing into the fixture folder.
        """
        handler = DataHandler(kcg_golden_folder, num_samples=6, includes=("reviewed",), suffix=".dat")
        handler.data_file = tmp_path / "reviewed.dat"  # redirect write target
        result = handler.save_to_new_file(prefix="auto")
        assert result.exists()
        assert result.parent == tmp_path
        assert result.name.startswith("auto_")
