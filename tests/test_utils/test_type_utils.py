"""
Tests for olaf.utils.type_utils

Functions under test:
    - ensure_list(value)

Reference: olaf/utils/type_utils.py
"""

from __future__ import annotations

import pytest

from olaf.utils.type_utils import ensure_list


class TestEnsureList:
    def test_list_passthrough(self) -> None:
        """ensure_list([1, 2, 3]) returns the same list object."""
        original = [1, 2, 3]
        result = ensure_list(original)
        assert result is original
        assert result == [1, 2, 3]

    def test_empty_list_passthrough(self) -> None:
        """ensure_list([]) returns the empty list unchanged."""
        original: list = []
        assert ensure_list(original) is original

    def test_string_repr_of_list(self) -> None:
        """ensure_list('[1, 2, 3]') -> [1, 2, 3] via ast.literal_eval."""
        assert ensure_list("[1, 2, 3]") == [1, 2, 3]

    def test_string_repr_of_nested_list(self) -> None:
        """Nested literals also round-trip."""
        assert ensure_list("[[1, 2], [3, 4]]") == [[1, 2], [3, 4]]

    def test_string_repr_of_tuple_of_tuples(self) -> None:
        """
        The 'changes' column in reviewed .dat is serialized as a tuple-of-tuples
        repr. ensure_list must handle that without crashing.
        """
        assert ensure_list("[(0, 1, 5), (1, -1, 7)]") == [(0, 1, 5), (1, -1, 7)]

    def test_invalid_string_raises_value_error(self) -> None:
        """
        ensure_list('not a list') raises ValueError from ast.literal_eval.
        Pin current behavior so any future signature change (e.g., returning
        the raw string) is intentional.
        """
        with pytest.raises((ValueError, SyntaxError)):
            ensure_list("not a list")

    def test_none_input_passthrough(self) -> None:
        """Non-string, non-list input is returned unchanged."""
        assert ensure_list(None) is None
        assert ensure_list(42) == 42
        assert ensure_list({"a": 1}) == {"a": 1}
