"""Tests for mathematical utility functions."""

import numpy as np
import pytest

from olaf.utils.math_utils import inps_L_to_ml, inps_ml_to_L, rms


class TestInpsConversions:
    """Test suite for INP concentration unit conversions."""

    def test_inps_ml_to_L_basic(self):
        """Test basic conversion from INPs/mL to INPs/L."""
        result = inps_ml_to_L(
            inps_col=10.0, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0
        )
        expected = (10.0 * 10.0) / (620.48 * 1.0)
        assert pytest.approx(result, rel=1e-6) == expected

    def test_inps_L_to_ml_basic(self):
        """Test basic conversion from INPs/L to INPs/mL."""
        result = inps_L_to_ml(
            inps_col=0.161, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0
        )
        expected = (0.161 * 620.48 * 1.0) / 10.0
        assert pytest.approx(result, rel=1e-3) == expected

    def test_inps_conversions_are_inverse(self):
        """Test that ml_to_L and L_to_ml are inverse operations."""
        original_inps_ml = 10.0
        vol_air_filt = 620.48
        prop_filter_used = 1.0
        vol_susp = 10.0

        # Convert to L then back to mL
        inps_L = inps_ml_to_L(original_inps_ml, vol_air_filt, prop_filter_used, vol_susp)
        inps_ml_result = inps_L_to_ml(inps_L, vol_air_filt, prop_filter_used, vol_susp)

        assert pytest.approx(inps_ml_result, rel=1e-10) == original_inps_ml

    def test_inps_ml_to_L_with_partial_filter(self):
        """Test conversion when only part of filter is used."""
        result = inps_ml_to_L(
            inps_col=10.0, vol_air_filt=620.48, prop_filter_used=0.5, vol_susp=10.0
        )
        # Using half the filter should double the concentration
        full_filter_result = inps_ml_to_L(
            inps_col=10.0, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0
        )
        assert pytest.approx(result, rel=1e-6) == full_filter_result * 2

    def test_inps_ml_to_L_zero_inps(self):
        """Test conversion with zero INPs."""
        result = inps_ml_to_L(
            inps_col=0.0, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0
        )
        assert result == 0.0

    def test_inps_L_to_ml_zero_inps(self):
        """Test conversion with zero INPs."""
        result = inps_L_to_ml(
            inps_col=0.0, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0
        )
        assert result == 0.0

    def test_inps_ml_to_L_different_suspension_volumes(self):
        """Test that larger suspension volume increases INPs/L proportionally."""
        vol_susp_1 = 10.0
        vol_susp_2 = 20.0
        inps_col = 10.0

        result_1 = inps_ml_to_L(inps_col, 620.48, 1.0, vol_susp_1)
        result_2 = inps_ml_to_L(inps_col, 620.48, 1.0, vol_susp_2)

        # Double suspension volume should double INPs/L
        assert pytest.approx(result_2, rel=1e-6) == result_1 * 2


class TestRMS:
    """Test suite for root mean square calculations."""

    def test_rms_simple_array(self):
        """Test RMS with a simple integer array."""
        result = rms([1, 2, 3, 4, 5])
        expected = np.sqrt(np.mean([1, 4, 9, 16, 25]))
        assert pytest.approx(result, rel=1e-10) == expected

    def test_rms_zeros(self):
        """Test RMS with array of zeros."""
        result = rms([0, 0, 0, 0])
        assert result == 0.0

    def test_rms_single_value(self):
        """Test RMS with single value."""
        result = rms([5.0])
        assert result == 5.0

    def test_rms_negative_values(self):
        """Test RMS with negative values (should square them)."""
        result = rms([-3, -4])
        expected = np.sqrt((9 + 16) / 2)
        assert pytest.approx(result, rel=1e-10) == expected

    def test_rms_mixed_signs(self):
        """Test RMS with mixed positive and negative values."""
        result = rms([-2, 2])
        expected = np.sqrt((4 + 4) / 2)
        assert pytest.approx(result, rel=1e-10) == expected

    def test_rms_numpy_array(self):
        """Test RMS accepts numpy arrays."""
        arr = np.array([1, 2, 3, 4, 5])
        result = rms(arr)
        expected = np.sqrt(np.mean([1, 4, 9, 16, 25]))
        assert pytest.approx(result, rel=1e-10) == expected

    def test_rms_large_values(self):
        """Test RMS with large values."""
        result = rms([1000, 2000, 3000])
        expected = np.sqrt(np.mean([1000**2, 2000**2, 3000**2]))
        assert pytest.approx(result, rel=1e-10) == expected
