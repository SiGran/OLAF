"""
Tests for olaf.utils.math_utils

Functions under test:
    - inps_ml_to_L(inps_col, vol_air_filt, prop_filter_used, vol_susp)
    - inps_L_to_ml(inps_col, vol_air_filt, prop_filter_used, vol_susp)
    - rms(x)

Reference: olaf/utils/math_utils.py
"""

from __future__ import annotations

import pytest

# from olaf.utils.math_utils import inps_L_to_ml, inps_ml_to_L, rms


class TestUnitConversion:
    def test_roundtrip_scalar(self) -> None:
        """ml -> L -> ml returns the original value (within float tolerance)."""
        pytest.skip("not implemented")

    def test_roundtrip_series(self) -> None:
        """Same as scalar, but with a pandas Series input."""
        pytest.skip("not implemented")

    def test_inps_L_to_ml_known_value(self) -> None:
        """
        Hand-computed example:
            inps_L=100, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10
            -> 100 * 620.48 * 1.0 / 10 = 6204.8 inps/mL
        Source: olaf/utils/math_utils.py:8-9
        """
        pytest.skip("not implemented")

    def test_inps_ml_to_L_known_value(self) -> None:
        """Reverse of above."""
        pytest.skip("not implemented")


class TestRms:
    def test_list_input(self) -> None:
        """rms([3, 4]) == sqrt((9+16)/2) ~= 3.5355..."""
        pytest.skip("not implemented")

    def test_series_input(self) -> None:
        pytest.skip("not implemented")

    def test_single_value(self) -> None:
        """rms([x]) == |x|"""
        pytest.skip("not implemented")

    def test_empty_input_behavior(self) -> None:
        """
        Pin current behavior: rms([]) returns nan with a RuntimeWarning.
        (Document so changes are intentional.)
        """
        pytest.skip("not implemented")
