"""
This module contains the tests for the SpacedTempCSV class.
"""

from pathlib import Path

import pandas as pd
import pytest

from olaf.processing.spaced_temp_csv import SpacedTempCSV


class TestSpacedTempCSV:
    @pytest.fixture(scope="session")
    def setup_files(self):
        # Load the input and expected output files
        expected_output_file = (
            Path.cwd().parent
            / "test_data"
            / "SGP 2.21.24 base"
            / "test1_changed_frozen_at_temp_sgp men 02.21.24 a base.csv"
        )
        input_path = Path.cwd().parent / "test_data" / "SGP 2.21.24 base"
        if not expected_output_file.exists():
            expected_output_file = (
                Path.cwd()
                / "tests"
                / "test_data"
                / "SGP 2.21.24 base"
                / "test1_changed_frozen_at_temp_sgp men 02.21.24 a base.csv"
            )
            input_path = Path.cwd() / "tests" / "test_data" / "SGP 2.21.24 base"

        expected_output_data = pd.read_csv(expected_output_file)
        return input_path, expected_output_data

    def test_create_temp_csv(self, setup_files):
        dict_samples_to_dilution = {
            "Sample_5": 1,
            "Sample_4": 11,
            "Sample_3": 121,
            "Sample_2": 1331,
            "Sample_1": 14641,
            "Sample_0": float("inf"),
        }
        input_path, expected_output_data = setup_files

        # Create an instance of the class
        processor = SpacedTempCSV(input_path, num_samples=6, includes=("test1", "reviewed"))

        # Call the create_temp_csv function
        generated_output_file = processor.create_temp_csv(dict_samples_to_dilution, save=False)

        # Compare the generated output with the expected output
        pd.testing.assert_frame_equal(generated_output_file, expected_output_data)
