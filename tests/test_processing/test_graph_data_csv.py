"""Tests for GraphDataCSV class - core INP calculations."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from olaf.processing.graph_data_csv import GraphDataCSV


class TestGraphDataCSVInitialization:
    """Test suite for GraphDataCSV initialization."""

    @pytest.fixture
    def test_folder(self):
        """Return path to test data folder."""
        test_data_path = Path.cwd() / "tests" / "test_data" / "SGP 2.21.24 base"
        if not test_data_path.exists():
            test_data_path = Path.cwd().parent / "test_data" / "SGP 2.21.24 base"
        return test_data_path

    @pytest.fixture
    def sample_dilution_dict(self):
        """Sample dilution dictionary for tests."""
        return {
            "Sample_5": 1,
            "Sample_4": 11,
            "Sample_3": 121,
            "Sample_2": 1331,
            "Sample_1": 14641,
            "Sample_0": float("inf"),
        }

    def test_initialization_renames_columns(self, test_folder, sample_dilution_dict):
        """Test that initialization properly renames columns to dilution factors."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("frozen_at_temp", "reviewed"),
        )

        # Check that columns were renamed from Sample_X to dilution factors
        assert 1 in processor.data.columns
        assert 11 in processor.data.columns
        assert 121 in processor.data.columns
        assert "degC" in processor.data.columns

    def test_initialization_stores_parameters(self, test_folder, sample_dilution_dict):
        """Test that initialization stores all required parameters."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        assert processor.sample_type == "ambient"
        assert processor.vol_air_filt == 620.48
        assert processor.wells_per_sample == 32
        assert processor.filter_used == 1.0
        assert processor.vol_susp == 10.0


class TestConvertINPsL:
    """Test suite for convert_INPs_L method."""

    @pytest.fixture
    def test_folder(self):
        """Return path to test data folder."""
        test_data_path = Path.cwd() / "tests" / "test_data" / "SGP 2.21.24 base"
        if not test_data_path.exists():
            test_data_path = Path.cwd().parent / "test_data" / "SGP 2.21.24 base"
        return test_data_path

    @pytest.fixture
    def sample_dilution_dict(self):
        """Sample dilution dictionary for tests."""
        return {
            "Sample_5": 1,
            "Sample_4": 11,
            "Sample_3": 121,
            "Sample_2": 1331,
            "Sample_1": 14641,
            "Sample_0": float("inf"),
        }

    @pytest.fixture
    def sample_header(self):
        """Sample header dictionary for tests."""
        return {
            "site": "SGP",
            "start_time": "2024-02-21 10:00:00",
            "end_time": "2024-02-21 22:00:00",
            "filter_color": "blue",
            "treatment": ("base",),
        }

    def test_convert_INPs_L_returns_dataframe(
        self, test_folder, sample_dilution_dict, sample_header
    ):
        """Test that convert_INPs_L returns a DataFrame."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        result = processor.convert_INPs_L(sample_header, save=False, show_plot=False)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_convert_INPs_L_has_required_columns(
        self, test_folder, sample_dilution_dict, sample_header
    ):
        """Test that output has required columns."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        result = processor.convert_INPs_L(sample_header, save=False, show_plot=False)

        # Check for essential columns
        assert "degC" in result.columns
        assert "INPS_L" in result.columns
        assert "lower_CI" in result.columns
        assert "upper_CI" in result.columns

    def test_convert_INPs_L_decreasing_temperature(
        self, test_folder, sample_dilution_dict, sample_header
    ):
        """Test that temperatures are in decreasing order."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        result = processor.convert_INPs_L(sample_header, save=False, show_plot=False)

        temperatures = result["degC"].values
        # Check that temperatures are decreasing (more negative)
        assert all(temperatures[i] >= temperatures[i + 1] for i in range(len(temperatures) - 1))

    def test_convert_INPs_L_positive_inps_values(
        self, test_folder, sample_dilution_dict, sample_header
    ):
        """Test that INPs/L values are positive."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        result = processor.convert_INPs_L(sample_header, save=False, show_plot=False)

        # All INPs/L values should be positive (excluding NaN)
        valid_inps = result["INPS_L"].dropna()
        assert all(valid_inps > 0)

    def test_convert_INPs_L_confidence_intervals_valid(
        self, test_folder, sample_dilution_dict, sample_header
    ):
        """Test that confidence intervals are valid."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        result = processor.convert_INPs_L(sample_header, save=False, show_plot=False)

        # Lower CI should be less than INPS_L
        valid_rows = result.dropna(subset=["INPS_L", "lower_CI"])
        if not valid_rows.empty:
            assert all(valid_rows["lower_CI"] <= valid_rows["INPS_L"])

        # Upper CI should be greater than INPS_L
        valid_rows = result.dropna(subset=["INPS_L", "upper_CI"])
        if not valid_rows.empty:
            assert all(valid_rows["upper_CI"] >= valid_rows["INPS_L"])

    def test_convert_INPs_L_monotonically_increasing(
        self, test_folder, sample_dilution_dict, sample_header
    ):
        """Test that INPs/L increases as temperature decreases."""
        if not test_folder.exists():
            pytest.skip("Test data folder not found")

        processor = GraphDataCSV(
            folder_path=test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
        )

        result = processor.convert_INPs_L(sample_header, save=False, show_plot=False)

        # Remove NaN values
        valid_data = result.dropna(subset=["INPS_L"])

        if len(valid_data) > 1:
            # INPs should generally increase as temperature decreases
            # (allowing for some noise in experimental data)
            inps_values = valid_data["INPS_L"].values

            # Check that most consecutive pairs show increase
            increases = sum(
                inps_values[i + 1] >= inps_values[i] for i in range(len(inps_values) - 1)
            )
            total_pairs = len(inps_values) - 1

            # Allow some variance, but expect majority to increase
            assert increases / total_pairs > 0.6


class TestINPCalculationLogic:
    """Test the mathematical logic of INP calculations."""

    def test_zero_frozen_wells_gives_low_inps(self):
        """Test that zero frozen wells gives low/near-zero INPs."""
        # This is a conceptual test - would need mock data
        # If no wells freeze, INPs should be very low
        pass  # Placeholder for future implementation

    def test_all_frozen_wells_handled(self):
        """Test handling when all wells are frozen."""
        # When all wells freeze, the calculation should handle this edge case
        pass  # Placeholder for future implementation

    def test_dilution_series_selection(self):
        """Test that appropriate dilution is selected at each temperature."""
        # The algorithm should select the most reliable dilution
        # (not too dilute, not all frozen)
        pass  # Placeholder for future implementation
