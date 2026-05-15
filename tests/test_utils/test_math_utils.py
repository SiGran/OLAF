"""
Tests for olaf.utils.math_utils

Functions under test:
    - inps_ml_to_L(inps_col, vol_air_filt, prop_filter_used, vol_susp)
    - inps_L_to_ml(inps_col, vol_air_filt, prop_filter_used, vol_susp)
    - rms(x)

Reference: olaf/utils/math_utils.py
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from olaf.utils.math_utils import inps_L_to_ml, inps_ml_to_L, rms


class TestUnitConversion:
    def test_roundtrip_scalar(self) -> None:
        """ml -> L -> ml returns the original value (within float tolerance)."""
        original = 1234.5
        params = dict(vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10)
        round_trip = inps_L_to_ml(inps_ml_to_L(original, **params), **params)
        assert round_trip == pytest.approx(original, rel=1e-12)

    def test_roundtrip_series(self) -> None:
        """Same as scalar, but with a pandas Series input."""
        original = pd.Series([10.0, 100.0, 1000.0])
        params = dict(vol_air_filt=620.48, prop_filter_used=0.5, vol_susp=10)
        round_trip = inps_L_to_ml(inps_ml_to_L(original, **params), **params)
        pd.testing.assert_series_equal(round_trip, original, rtol=1e-12)

    def test_inps_L_to_ml_known_value(self) -> None:
        """
        Hand-computed example:
            inps_L=100, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10
            -> 100 * 620.48 * 1.0 / 10 = 6204.8 inps/mL
        Source: olaf/utils/math_utils.py:8-9
        """
        assert inps_L_to_ml(100, 620.48, 1.0, 10) == pytest.approx(6204.8)

    def test_inps_ml_to_L_known_value(self) -> None:
        """Reverse of above: 6204.8 inps/mL -> 100 inps/L."""
        assert inps_ml_to_L(6204.8, 620.48, 1.0, 10) == pytest.approx(100.0)

    def test_proportion_filter_used_scales_inversely(self) -> None:
        """Halving prop_filter_used doubles the effective filtered volume divisor."""
        full = inps_L_to_ml(100, 620.48, 1.0, 10)
        half = inps_L_to_ml(100, 620.48, 0.5, 10)
        assert half == pytest.approx(full * 0.5)


class TestRms:
    def test_list_input(self) -> None:
        """rms([3, 4]) == sqrt((9+16)/2) == sqrt(12.5)"""
        assert rms([3, 4]) == pytest.approx(np.sqrt(12.5))

    def test_series_input(self) -> None:
        """rms accepts a pandas Series."""
        assert rms(pd.Series([3.0, 4.0])) == pytest.approx(np.sqrt(12.5))

    def test_numpy_array_input(self) -> None:
        """rms accepts a numpy array."""
        assert rms(np.array([3.0, 4.0])) == pytest.approx(np.sqrt(12.5))

    def test_single_value(self) -> None:
        """rms([x]) == |x|"""
        assert rms([5.0]) == pytest.approx(5.0)
        assert rms([-5.0]) == pytest.approx(5.0)

    def test_all_zeros(self) -> None:
        """rms of zeros is zero."""
        assert rms([0.0, 0.0, 0.0]) == 0.0

    def test_empty_input_returns_nan(self) -> None:
        """
        Pin current behavior: rms([]) returns nan with a RuntimeWarning
        (numpy mean of empty slice).
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = rms([])
        assert np.isnan(result)
