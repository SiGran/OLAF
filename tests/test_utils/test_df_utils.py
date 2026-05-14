"""
Tests for olaf.utils.df_utils

Functions under test:
    - read_with_flexible_header(file_path, expected_columns, max_rows)
    - header_to_dict(header_lines)
    - unique_dilutions(series)

Reference: olaf/utils/df_utils.py
"""

from __future__ import annotations

import pytest

# from olaf.utils.df_utils import header_to_dict, read_with_flexible_header, unique_dilutions


class TestHeaderToDict:
    def test_well_formed_lines(self) -> None:
        """
        Given: a list of "key = value" lines
        When:  header_to_dict is called
        Then:  returns a dict with each key/value parsed correctly

        Source: olaf/utils/df_utils.py:32-45
        """
        # TODO: arrange minimal header lines list
        # TODO: act -> header_to_dict(...)
        # TODO: assert dict equality
        pytest.skip("not implemented")

    def test_string_input_is_split_on_newlines(self) -> None:
        """
        Given: a single string containing newline-separated "k = v" lines
        When:  header_to_dict is called
        Then:  string is splitlines()'d and parsed into dict
        """
        pytest.skip("not implemented")

    def test_value_containing_equals_is_preserved(self) -> None:
        """
        Given: a line like "expr = a = b" (value contains ' = ')
        When:  header_to_dict is called
        Then:  key is "expr", value is "a = b" (split with maxsplit=1)
        """
        pytest.skip("not implemented")

    def test_malformed_line_does_not_raise(self, capsys: pytest.CaptureFixture[str]) -> None:
        """
        Given: a line missing ' = '
        When:  header_to_dict is called
        Then:  the line is skipped and a message is printed to stdout
               (current behavior - may move to logging later)
        """
        pytest.skip("not implemented")

    def test_real_header_from_sgp_file(self, sgp_test_folder) -> None:
        """
        Given: header lines from tests/test_data/SGP 2.21.24 base/INPs_L_*.csv
        When:  header_to_dict is called
        Then:  contains keys site, start_time, end_time, treatment, vol_air_filt, ...

        Real data: SGP 2.21.24 base/INPs_L_frozen_at_temp_test1_reviewed_*.csv
        """
        pytest.skip("not implemented")


class TestReadWithFlexibleHeader:
    def test_reads_file_with_short_header(self, sgp_test_folder) -> None:
        """
        Given: an INPs_L_*.csv from SGP 2.21.24 base
        When:  read_with_flexible_header(file) is called with default expected_columns
        Then:  returns (header_lines: list[str], df: pd.DataFrame) where df has the
               expected columns and header_lines contains every line before the column row.
        """
        pytest.skip("not implemented")

    def test_reads_file_with_qc_flag_column(self, capek_project_folder) -> None:
        """
        Given: a blank_corrected_*.csv (has additional 'qc_flag' column)
        When:  read_with_flexible_header(file, expected_columns=(..., "qc_flag"))
        Then:  parses correctly.

        Real data: capek/KCG 7.09.24 base/blank_corrected_*.csv
        """
        pytest.skip("not implemented")

    def test_missing_expected_columns_warns_and_returns_empty(
        self, tmp_path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Given: a CSV whose column row never matches expected_columns
        When:  read_with_flexible_header is called
        Then:  prints "No columns ... found" and still returns a tuple
               (current behavior - pin it).
        """
        pytest.skip("not implemented")


class TestUniqueDilutions:
    def test_integer_series(self) -> None:
        """Given a Series of int-likes, returns a sorted tuple of ints."""
        pytest.skip("not implemented")

    def test_float_series_with_inf(self) -> None:
        """Given floats including float('inf'), inf is preserved."""
        pytest.skip("not implemented")

    def test_tuples_in_series_are_flattened(self) -> None:
        """
        Given: Series with cells that are tuples (e.g. blank_correction stores
               unique_dilutions output as a tuple per row)
        When:  unique_dilutions is called
        Then:  every element of every tuple is collected, deduped and sorted.
        """
        pytest.skip("not implemented")

    def test_mixed_types_fall_back_to_original_value(self) -> None:
        """Given a non-numeric string, it is kept as-is in the result tuple."""
        pytest.skip("not implemented")

    def test_returns_sorted_tuple(self) -> None:
        """Output is always sorted ascending."""
        pytest.skip("not implemented")
