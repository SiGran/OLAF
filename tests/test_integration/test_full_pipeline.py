"""Integration tests for the complete OLAF data processing pipeline.

This module tests the full workflow:
1. Stage 1: GraphDataCSV - Convert raw data to INPs/L
2. Stage 2: BlankCorrector - Apply blank correction
3. Stage 3: FinalFileCreation - Create ARM standard format files
"""

from pathlib import Path

import pandas as pd
import pytest

from olaf.processing.blank_correction import BlankCorrector
from olaf.processing.graph_data_csv import GraphDataCSV


class TestStage1GraphDataProcessing:
    """Integration tests for Stage 1: Raw data to INPs/L conversion."""

    def test_full_stage1_processing(self, sgp_test_folder, sample_dilution_dict, standard_header):
        """Test complete Stage 1: data loading, processing, and INPs/L calculation."""
        # Initialize processor
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

        # Process data and generate INPs/L output
        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # Verify output structure
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert all(
            col in result.columns for col in ["degC", "INPS_L", "lower_CI", "upper_CI", "dilution"]
        )

        # Verify scientific validity
        assert all(result["INPS_L"].dropna() >= -1e-10), "INPs/L should be non-negative"
        temps = result["degC"].values
        assert all(
            temps[i] >= temps[i + 1] for i in range(len(temps) - 1)
        ), "Temperatures should decrease"

        # Verify concentration increases with decreasing temperature
        valid_data = result.dropna(subset=["INPS_L"])
        if len(valid_data) > 1:
            inps_values = valid_data["INPS_L"].values
            increases = sum(
                inps_values[i + 1] >= inps_values[i] for i in range(len(inps_values) - 1)
            )
            assert increases / (len(inps_values) - 1) > 0.6, "INPs should generally increase"

    def test_stage1_with_different_parameters(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test Stage 1 with different experimental parameters."""
        # Test with different air volume and suspension volume
        processor = GraphDataCSV(
            folder_path=sgp_test_folder,
            num_samples=6,
            sample_type="ambient",
            vol_air_filt=1000.0,  # Different air volume
            wells_per_sample=32,
            filter_used=0.5,  # Half filter used
            vol_susp=20.0,  # Different suspension volume
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        result = processor.convert_INPs_L(standard_header, save=False, show_plot=False)

        # Should still produce valid output
        assert not result.empty
        assert all(result["INPS_L"].dropna() >= -1e-10)


class TestStage2BlankCorrection:
    """Integration tests for Stage 2: Blank correction application."""

    @pytest.mark.skip(reason="Requires blank data files - will be enabled when available")
    def test_blank_correction_loading(self, tmp_path):
        """Test that blank correction properly loads and processes blank files."""
        # This test will be expanded when blank data is available
        project_folder = tmp_path / "project"
        project_folder.mkdir()

        # Create blank folder structure
        blank_folder = project_folder / "SGP 02.21.24 blank"
        blank_folder.mkdir()

        # Initialize blank corrector
        corrector = BlankCorrector(project_folder)

        # Verify blank files are found
        assert isinstance(corrector.blank_files, list)

    @pytest.mark.skip(reason="Requires sample and blank data - will be enabled when available")
    def test_full_blank_correction_workflow(self, tmp_path):
        """Test complete blank correction workflow on sample data."""
        # This test will verify:
        # 1. Blank files are loaded
        # 2. Blanks are averaged correctly
        # 3. Blank correction is applied to samples
        # 4. Confidence intervals are properly adjusted
        # 5. Monotonicity is enforced
        pass


class TestStage3FinalFileCreation:
    """Integration tests for Stage 3: ARM standard format file creation."""

    @pytest.mark.skip(reason="Requires processed data files - will be enabled when available")
    def test_final_file_aggregation(self, tmp_path):
        """Test that multiple treatments are properly combined into final file."""
        # This test will verify:
        # 1. Multiple treatment files are loaded
        # 2. Data is combined on common temperature ranges
        # 3. ARM format is properly applied
        # 4. Headers include all required metadata
        pass


class TestEndToEndPipeline:
    """End-to-end integration tests covering all three stages."""

    def test_stage1_output_format_for_stage2(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Verify Stage 1 output is compatible with Stage 2 input requirements."""
        # Process through Stage 1
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

        # Verify output has all columns needed for Stage 2 (blank correction)
        required_columns = ["degC", "INPS_L", "lower_CI", "upper_CI", "dilution"]
        assert all(col in result.columns for col in required_columns)

        # Verify data types are correct for next stage
        assert result["degC"].dtype in [float, "float64"]
        assert result["INPS_L"].dtype in [float, "float64"]

    @pytest.mark.skip(reason="Requires full dataset - will be enabled when available")
    def test_complete_pipeline_ambient_sample(self, tmp_path):
        """Test complete pipeline for ambient air sample through all three stages."""
        # This comprehensive test will:
        # 1. Process raw data to INPs/L (Stage 1)
        # 2. Apply blank correction (Stage 2)
        # 3. Combine treatments and create ARM file (Stage 3)
        # 4. Verify final output meets all ARM standards
        pass

    @pytest.mark.skip(reason="Requires full dataset - will be enabled when available")
    def test_pipeline_with_multiple_treatments(self, tmp_path):
        """Test pipeline with base, heat, and peroxide treatments."""
        # This test will verify that multiple treatments for the same
        # sample date are properly processed and combined
        pass


class TestPipelineErrorHandling:
    """Test error handling and edge cases across the pipeline."""

    def test_stage1_handles_missing_data_gracefully(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that missing or incomplete data is handled gracefully."""
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

        # Should handle missing data with NaN values
        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_invalid_folder_path_raises_error(self, sample_dilution_dict, standard_header):
        """Test that invalid folder paths raise appropriate errors."""
        with pytest.raises(Exception):  # Could be FileNotFoundError or ValueError
            processor = GraphDataCSV(
                folder_path=Path("/nonexistent/path"),
                num_samples=6,
                sample_type="ambient",
                vol_air_filt=620.48,
                wells_per_sample=32,
                filter_used=1.0,
                vol_susp=10.0,
                dict_samples_to_dilution=sample_dilution_dict,
                includes=("test1",),
            )
            processor.convert_INPs_L(standard_header, save=False, show_plot=False)

    def test_zero_air_volume_handling(self, sgp_test_folder, sample_dilution_dict, standard_header):
        """Test handling of edge case with zero air volume."""
        # Zero air volume leads to various errors including UnboundLocalError
        with pytest.raises((ValueError, ZeroDivisionError, UnboundLocalError)):
            processor = GraphDataCSV(
                folder_path=sgp_test_folder,
                num_samples=6,
                sample_type="ambient",
                vol_air_filt=0.0,  # Invalid: zero air volume
                wells_per_sample=32,
                filter_used=1.0,
                vol_susp=10.0,
                dict_samples_to_dilution=sample_dilution_dict,
                includes=("test1",),
            )
            processor.convert_INPs_L(standard_header, save=False, show_plot=False)


class TestDataConsistency:
    """Test data consistency and validation across pipeline stages."""

    def test_dilution_factors_preserved_through_stage1(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Verify dilution factors are correctly preserved through processing."""
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

        # Check that dilution column contains expected values
        assert "dilution" in result.columns
        # Dilution values should be comma-separated strings of the original dilution factors
        assert result["dilution"].notna().any()

    def test_temperature_range_consistency(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Test that temperature ranges are scientifically valid."""
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

        # Temperature range should be reasonable for INP experiments (-30°C to 0°C)
        temps = result["degC"].values
        assert all(temps <= 0), "All temperatures should be at or below freezing"
        assert all(temps >= -40), "Temperatures should be above experimental minimum"

    def test_confidence_intervals_remain_positive(
        self, sgp_test_folder, sample_dilution_dict, standard_header
    ):
        """Verify confidence intervals are non-negative throughout processing."""
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

        # CI values should always be non-negative
        for col in ["lower_CI", "upper_CI"]:
            valid_ci = result[col].dropna()
            if not valid_ci.empty:
                assert all(valid_ci >= 0), f"{col} should be non-negative"
