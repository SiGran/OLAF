"""Pytest configuration and shared fixtures for OLAF tests."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_root():
    """Return the root path for test data.

    This fixture locates the test_data directory regardless of where
    pytest is run from.
    """
    # Try multiple possible locations
    possible_paths = [
        Path(__file__).parent / "test_data",  # tests/test_data
        Path.cwd() / "tests" / "test_data",    # running from project root
        Path.cwd() / "test_data",              # running from tests/
    ]

    for path in possible_paths:
        if path.exists():
            return path

    pytest.fail(f"Could not locate test_data directory. Tried: {possible_paths}")


@pytest.fixture(scope="session")
def sgp_test_folder(test_data_root):
    """Return path to SGP 2.21.24 base test folder."""
    folder = test_data_root / "SGP 2.21.24 base"
    if not folder.exists():
        pytest.fail(f"Test data folder not found: {folder}")
    return folder


@pytest.fixture(scope="session")
def sample_dilution_dict():
    """Standard dilution dictionary used in SGP test data."""
    return {
        "Sample_5": 1,
        "Sample_4": 11,
        "Sample_3": 121,
        "Sample_2": 1331,
        "Sample_1": 14641,
        "Sample_0": float("inf"),
    }


@pytest.fixture(scope="session")
def standard_header():
    """Standard header dictionary for test data."""
    return {
        "site": "SGP",
        "start_time": "2024-02-21 10:00:00",
        "end_time": "2024-02-21 22:00:00",
        "filter_color": "blue",
        "treatment": ("base",),
        "user": "Test User",
        "IS": "IS3a",
        "vol_air_filt": "620.48",
        "wells_per_sample": "32",
        "proportion_filter_used": "1.0",
        "vol_susp": "10",
    }
