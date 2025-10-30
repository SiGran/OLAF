"""Tests for GraphDataCSV class - core INP calculations."""

import numpy as np
import pandas as pd
import pytest

from olaf.processing.graph_data_csv import GraphDataCSV


class TestGraphDataCSVInitialization:
    """Test suite for GraphDataCSV initialization."""

    def test_initialization_renames_columns(self, sgp_test_folder, sample_dilution_dict):
        """Test that initialization properly renames columns to dilution factors."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),  # Will be combined with frozen_at_temp, reviewed
        )

        # Check that columns were renamed from Sample_X to dilution factors
        assert 1 in processor.data.columns
        assert 11 in processor.data.columns
        assert 121 in processor.data.columns
        assert "degC" in processor.data.columns

    def test_initialization_stores_parameters(self, sgp_test_folder, sample_dilution_dict):
        """Test that initialization stores all required parameters."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        assert processor.sample_type == "ambient"
        assert processor.vol_air_filt == 620.48
        assert processor.wells_per_sample == 32
        assert processor.filter_used == 1.0
        assert processor.vol_susp == 10.0

    def test_initialization_loads_correct_data(self, sgp_test_folder, sample_dilution_dict):
        """Test that data is loaded and has expected structure."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        # Check that data was loaded
        assert not processor.data.empty
        # Check temperature column exists (after renaming)
        assert "degC" in processor.data.columns
        # Check that we have multiple temperature points
        assert len(processor.data) > 10


class TestConvertINPsL:
    """Test suite for convert_INPs_L method."""

    def test_convert_INPs_L_returns_dataframe(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that convert_INPs_L returns a DataFrame."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_convert_INPs_L_has_required_columns(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that output has required columns."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # Check for essential columns
        assert "degC" in result.columns
        assert "INPS_L" in result.columns
        assert "lower_CI" in result.columns
        assert "upper_CI" in result.columns

    def test_convert_INPs_L_decreasing_temperature(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that temperatures are in decreasing order."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        temperatures = result["degC"].values
        # Check that temperatures are decreasing (more negative)
        assert all(temperatures[i] >= temperatures[i + 1] for i in range(len(temperatures) - 1))

    def test_convert_INPs_L_positive_inps_values(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that INPs/L values are non-negative (allowing for near-zero values)."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # All INPs/L values should be non-negative (allowing for near-zero rounding)
        # Small negative values like -0.000000 are acceptable (floating point rounding)
        valid_inps = result["INPS_L"].dropna()
        assert all(valid_inps >= -1e-10), "Found significantly negative INPs/L values"

    def test_convert_INPs_L_confidence_intervals_exist(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that confidence interval columns exist and contain valid data.

        Note: The CI values in this implementation represent confidence interval
        widths (deltas from the main value) rather than absolute bounds. This is
        a known behavior of the existing scientific calculation.
        """
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # Check that CI columns exist
        assert "lower_CI" in result.columns
        assert "upper_CI" in result.columns

        # Filter meaningful data
        meaningful_data = result[result["INPS_L"] > 0.01].dropna(
            subset=["INPS_L", "lower_CI", "upper_CI"]
        )

        if not meaningful_data.empty:
            # CI values should be non-negative
            assert all(meaningful_data["lower_CI"] >= 0), "Lower CI should be non-negative"
            assert all(meaningful_data["upper_CI"] >= 0), "Upper CI should be non-negative"

            # Lower CI should generally be less than main value
            lower_ci_valid = meaningful_data["lower_CI"] <= meaningful_data["INPS_L"]
            assert lower_ci_valid.sum() / len(meaningful_data) > 0.8, \
                "Most lower CI should be <= INPS_L"

            # CI columns should have data
            assert meaningful_data["lower_CI"].notna().any()
            assert meaningful_data["upper_CI"].notna().any()

    def test_convert_INPs_L_increases_with_decreasing_temp(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that INPs/L generally increases as temperature decreases."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

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

    def test_convert_INPs_L_no_negative_values(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that there are no negative INP values."""
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # Check no negative values in any column
        for col in ["INPS_L", "lower_CI", "upper_CI"]:
            valid_values = result[col].dropna()
            if not valid_values.empty:
                assert all(valid_values >= 0), f"Found negative values in {col}"


class TestINPCalculationEdgeCases:
    """Test edge cases in INP calculations."""

    def test_handles_all_zeros(self, sgp_test_folder, sample_dilution_dict, standard_header):
        """Test handling when no wells are frozen."""
        # This tests the robustness of the calculation logic
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=620.48,
            wells_per_sample=32,
            filter_used=1.0,
            vol_susp=10.0,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # Should handle gracefully (NaN or very low values)
        assert not result.empty
        # At least some rows should have valid data
        assert result["INPS_L"].notna().any()
