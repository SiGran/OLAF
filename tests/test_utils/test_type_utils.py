"""
Tests for olaf.utils.type_utils

Functions under test:
    - ensure_list(value)

Reference: olaf/utils/type_utils.py
"""

from __future__ import annotations

import pytest

# from olaf.utils.type_utils import ensure_list


class TestEnsureList:
    def test_list_passthrough(self) -> None:
        """ensure_list([1, 2, 3]) returns the same list (identity or equality)."""
        pytest.skip("not implemented")

    def test_string_repr_of_list(self) -> None:
        """ensure_list('[1, 2, 3]') -> [1, 2, 3] via ast.literal_eval."""
        pytest.skip("not implemented")

    def test_invalid_string_raises(self) -> None:
        """
        ensure_list('not a list') raises (ValueError or SyntaxError from literal_eval).
        Pin current behavior so changes are intentional.
        """
        pytest.skip("not implemented")

    def test_none_input_passthrough(self) -> None:
        """Non-string, non-list input is returned unchanged."""
        pytest.skip("not implemented")
