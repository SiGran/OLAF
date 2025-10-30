"""Tests for DataFrame utility functions."""

import pandas as pd
import pytest

from olaf.utils.df_utils import header_to_dict, read_with_flexible_header, unique_dilutions


class TestHeaderToDict:
    """Test suite for header_to_dict function."""

    def test_header_to_dict_basic(self):
        """Test basic header parsing."""
        header_lines = [
            "filename = test.csv",
            "site = SGP",
            "start_time = 2024-02-21 10:00:00",
            "end_time = 2024-02-21 22:00:00",
        ]
        result = header_to_dict(header_lines)

        assert result["filename"] == "test.csv"
        assert result["site"] == "SGP"
        assert result["start_time"] == "2024-02-21 10:00:00"
        assert result["end_time"] == "2024-02-21 22:00:00"

    def test_header_to_dict_empty(self):
        """Test with empty header lines."""
        result = header_to_dict([])
        assert result == {}

    def test_header_to_dict_with_spaces(self):
        """Test header parsing with extra spaces."""
        header_lines = [
            "filename  =  test.csv  ",
            "site = SGP",
        ]
        result = header_to_dict(header_lines)

        # The function splits on " = " (single space-equals-space)
        # Extra spaces before = become part of key, extra spaces after = become part of value
        assert result["filename "] == " test.csv  "
        assert result["site"] == "SGP"

    def test_header_to_dict_with_numeric_values(self):
        """Test header parsing with numeric values."""
        header_lines = [
            "num_samples = 6",
            "vol_air_filt = 620.48",
        ]
        result = header_to_dict(header_lines)

        # Values should be strings (not converted to numbers)
        assert result["num_samples"] == "6"
        assert result["vol_air_filt"] == "620.48"


class TestUniqueDilutions:
    """Test suite for unique_dilutions function."""

    def test_unique_dilutions_integers(self):
        """Test with integer dilution values."""
        series = pd.Series([1, 11, 121, 1, 11])
        result = unique_dilutions(series)

        assert result == (1, 11, 121)
        assert isinstance(result, tuple)

    def test_unique_dilutions_floats_as_integers(self):
        """Test that whole number floats are converted to integers."""
        series = pd.Series([1.0, 11.0, 121.0])
        result = unique_dilutions(series)

        # Should be integers, not floats
        assert result == (1, 11, 121)
        assert all(isinstance(x, int) for x in result)

    def test_unique_dilutions_with_tuples(self):
        """Test with tuple values in series."""
        series = pd.Series([
            (1,),
            (11,),
            (1,),
        ])
        result = unique_dilutions(series)

        # Should flatten tuples and return unique values
        assert 1 in result
        assert 11 in result

    def test_unique_dilutions_mixed_types(self):
        """Test with mixed numeric types."""
        series = pd.Series([1, 11.0, 121])
        result = unique_dilutions(series)

        assert set(result) == {1, 11, 121}

    def test_unique_dilutions_with_infinity(self):
        """Test handling of infinity values."""
        series = pd.Series([1, 11, float('inf')])
        result = unique_dilutions(series)

        assert 1 in result
        assert 11 in result
        assert float('inf') in result

    def test_unique_dilutions_sorted(self):
        """Test that results are sorted."""
        series = pd.Series([121, 1, 11])
        result = unique_dilutions(series)

        assert result == (1, 11, 121)

    def test_unique_dilutions_empty(self):
        """Test with empty series."""
        series = pd.Series([])
        result = unique_dilutions(series)

        assert result == tuple()


class TestReadWithFlexibleHeader:
    """Test suite for read_with_flexible_header function."""

    @pytest.fixture
    def temp_csv_with_header(self, tmp_path):
        """Create a temporary CSV file with header."""
        file_path = tmp_path / "test_data.csv"
        content = """filename = test.csv
site = SGP
start_time = 2024-02-21 10:00:00
end_time = 2024-02-21 22:00:00
degC,dilution,INPS_L,lower_CI,upper_CI
-5.0,1,100,90,110
-10.0,1,200,180,220
-15.0,1,300,270,330
"""
        file_path.write_text(content)
        return file_path

    def test_read_with_flexible_header_with_header(self, temp_csv_with_header):
        """Test reading CSV with metadata header."""
        header_lines, df = read_with_flexible_header(temp_csv_with_header)

        # Check header lines
        assert len(header_lines) == 4
        assert "filename = test.csv" in header_lines
        assert "site = SGP" in header_lines

        # Check DataFrame
        assert len(df) == 3
        assert "degC" in df.columns
        assert df["INPS_L"].tolist() == [100, 200, 300]

    def test_read_with_flexible_header_returns_dataframe(self, temp_csv_with_header):
        """Test that function returns a proper DataFrame."""
        _, df = read_with_flexible_header(temp_csv_with_header)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
