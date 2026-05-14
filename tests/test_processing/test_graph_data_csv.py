"""
Placeholder for olaf.processing.graph_data_csv tests.

This module is scheduled for a major rewrite (see TODO.md Phase 4). Per the
agreed plan, NO test bodies are scaffolded here yet — the rewrite will produce
a new public API, and characterization tests against the current buggy behavior
would be wasted effort.

Bugs from review that this module's eventual tests will cover:
    #1  prev_val == np.nan always False         (graph_data_csv.py:259, 261)
    #2  UnboundLocalError if last_4_i empty     (graph_data_csv.py:289-292)
    #8  Lost exception chaining (raise ... from e missing)  (graph_data_csv.py:78)

When the rewrite branch starts, replace this file with real test stubs
referencing the new API. Until then this single skip keeps the directory shape
stable and a CI signal that the placeholder still exists.
"""

import pytest

# from olaf.processing.graph_data_csv import GraphDataCSV


def test_graph_data_csv_rewrite_pending() -> None:
    """Placeholder until GraphDataCSV is rewritten — see TODO.md Phase 4."""
    pytest.skip("GraphDataCSV rewrite pending — see TODO.md Phase 4")
