"""
Tests for olaf.utils.df_utils

Functions under test:
    - read_with_flexible_header(file_path, expected_columns, max_rows)
    - header_to_dict(header_lines)
    - unique_dilutions(series)

Reference: olaf/utils/df_utils.py
"""

from __future__ import annotations

import pandas as pd
import pytest

from olaf.utils.df_utils import header_to_dict, read_with_flexible_header, unique_dilutions


class TestHeaderToDict:
    def test_well_formed_lines(self) -> None:
        """Given list of 'key = value' lines, returns dict."""
        lines = ["site = SGP", "treatment = base", "vol_air_filt = 620.48"]
        assert header_to_dict(lines) == {
            "site": "SGP",
            "treatment": "base",
            "vol_air_filt": "620.48",
        }

    def test_string_input_is_split_on_newlines(self) -> None:
        """String input is splitlines()'d before parsing."""
        s = "site = SGP\ntreatment = base\n"
        assert header_to_dict(s) == {"site": "SGP", "treatment": "base"}

    def test_value_containing_equals_is_preserved(self) -> None:
        """split(' = ', 1) preserves '=' in the value."""
        result = header_to_dict(["expr = a = b = c"])
        assert result == {"expr": "a = b = c"}

    def test_malformed_line_does_not_raise(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Line missing ' = ' is skipped; a warning message is printed."""
        result = header_to_dict(["valid = ok", "malformed-no-equals", "also = good"])
        assert result == {"valid": "ok", "also": "good"}
        captured = capsys.readouterr()
        assert "malformed-no-equals" in captured.out

    def test_empty_input_returns_empty_dict(self) -> None:
        """Edge case: empty list / empty string → empty dict."""
        assert header_to_dict([]) == {}
        assert header_to_dict("") == {}

    def test_real_header_from_capek_blank_corrected(self, capek_golden_folder) -> None:
        """
        Given: header lines from a real blank_corrected_*.csv in capek golden inputs.
        When:  header_to_dict is called.
        Then:  contains the expected metadata keys.

        Real data: goldens/inputs/capek/KCG 7.09.24 base/blank_corrected_10%_...csv
        """
        file = (
            capek_golden_folder
            / "KCG 7.09.24 base"
            / "blank_corrected_10%_error_threshold_INPs_L_frozen_at_temp_reviewed_capek 7.09.24 a base.csv"  # noqa: E501
        )
        if not file.exists():
            pytest.skip(f"Real fixture missing: {file}")
        header_lines, _df = read_with_flexible_header(file)
        result = header_to_dict(header_lines)
        for required in ("site", "start_time", "end_time", "treatment", "vol_air_filt"):
            assert required in result, f"missing key {required} in parsed header"
        assert result["site"] == "KCG"
        assert result["treatment"] == "base"


class TestReadWithFlexibleHeader:
    def test_reads_file_with_short_header(self, sgp_golden_folder) -> None:
        """
        This golden was curated without a metadata header (header_lines is empty).
        Then: df has expected columns.

        Real data: goldens/inputs/sgp_2_21_24_base/inps_L_expected.csv
        """
        file = sgp_golden_folder / "inps_L_expected.csv"
        if not file.exists():
            pytest.skip(f"Real fixture missing: {file}")
        header_lines, df = read_with_flexible_header(file)
        assert header_lines == []
        assert list(df.columns) == [
            "degC",
            "dilution",
            "INPS_L",
            "lower_CI",
            "upper_CI",
        ]
        assert len(df) > 0

    def test_reads_file_with_metadata_header(self, capek_golden_folder) -> None:
        """
        Capek blank_corrected files DO have metadata header lines before the column row.
        Then: header_lines collected; df parsed correctly.

        Real data: goldens/inputs/capek/KCG 7.09.24 base/blank_corrected_10%_...csv
        """
        file = (
            capek_golden_folder
            / "KCG 7.09.24 base"
            / "blank_corrected_10%_error_threshold_INPs_L_frozen_at_temp_reviewed_capek 7.09.24 a base.csv"  # noqa: E501
        )
        if not file.exists():
            pytest.skip(f"Real fixture missing: {file}")
        header_lines, df = read_with_flexible_header(file)
        assert len(header_lines) > 0
        assert any("site = KCG" in line for line in header_lines)
        assert list(df.columns) == [
            "degC",
            "dilution",
            "INPS_L",
            "lower_CI",
            "upper_CI",
        ]
        assert len(df) > 0

    def test_missing_expected_columns_warns_and_returns(
        self, tmp_path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Given: a CSV whose column row never matches expected_columns.
        Then:  prints 'No columns ... found'; still returns a tuple
               (current behavior - pin it).
        """
        bad = tmp_path / "bad.csv"
        bad.write_text("foo,bar,baz\n1,2,3\n4,5,6\n")
        header_lines, df = read_with_flexible_header(bad)
        captured = capsys.readouterr()
        assert "No columns" in captured.out
        # Header lines collect everything because no match was found
        assert "foo,bar,baz" in header_lines or any("foo,bar,baz" in line for line in header_lines)

    def test_custom_expected_columns(self, tmp_path) -> None:
        """expected_columns parameter is honored for non-default schemas."""
        f = tmp_path / "custom.csv"
        f.write_text("meta = info\na,b,c\n1,2,3\n4,5,6\n")
        header_lines, df = read_with_flexible_header(f, expected_columns=("a", "b", "c"))
        assert header_lines == ["meta = info"]
        assert list(df.columns) == ["a", "b", "c"]
        assert len(df) == 2


class TestUniqueDilutions:
    def test_integer_series(self) -> None:
        """Series of int-likes returns sorted tuple of ints."""
        result = unique_dilutions(pd.Series([1, 11, 121, 1, 11]))
        assert result == (1, 11, 121)

    def test_float_series_with_inf(self) -> None:
        """Floats including float('inf') are preserved (inf sorts last)."""
        result = unique_dilutions(pd.Series([1.0, 11.0, float("inf"), 121.0]))
        assert result == (1, 11, 121, float("inf"))

    def test_whole_floats_are_coerced_to_int(self) -> None:
        """A float whose value is a whole number is returned as int."""
        result = unique_dilutions(pd.Series([1.0, 2.0, 3.0]))
        assert result == (1, 2, 3)
        assert all(isinstance(v, int) for v in result)

    def test_non_whole_floats_kept_as_float(self) -> None:
        """1.5 stays a float."""
        result = unique_dilutions(pd.Series([1.0, 1.5, 2.0]))
        assert result == (1, 1.5, 2)

    def test_tuples_in_series_are_flattened(self) -> None:
        """
        Series cells that are tuples (e.g. blank_correction stores a tuple per
        row) get flattened — every element collected, deduped and sorted.
        """
        s = pd.Series([(1, 11), (11, 121), (121,)], dtype=object)
        result = unique_dilutions(s)
        assert result == (1, 11, 121)

    def test_lists_in_series_raise_type_error(self) -> None:
        """
        Pins current behavior: lists are unhashable, so pandas.Series.unique()
        raises TypeError before unique_dilutions can flatten them. Only tuples
        (hashable) work for the flatten path. Anchor for future generalization.
        """
        s = pd.Series([[1, 11], [11, 121]], dtype=object)
        with pytest.raises(TypeError, match="unhashable"):
            unique_dilutions(s)

    def test_returns_sorted_tuple(self) -> None:
        """Output is always sorted ascending."""
        result = unique_dilutions(pd.Series([121, 1, 11]))
        assert result == tuple(sorted(result))
        assert isinstance(result, tuple)
