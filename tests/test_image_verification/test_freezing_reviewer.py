"""
Tests for olaf.image_verification.freezing_reviewer (GUI smoke tests).

GUI tests are auto-skipped when no $DISPLAY is available (headless CI/servers).
Mark with @pytest.mark.gui (registered in pyproject.toml).

Class under test: FreezingReviewer(tk.Tk, folder_path, num_samples, wells_per_sample,
                                   dilution_dict, includes=...)
Inheritance chain: FreezingReviewer -> ButtonHandler -> DataLoader -> DataHandler
"""

from __future__ import annotations

import os

import pytest

# import tkinter as tk
# from olaf.image_verification.freezing_reviewer import FreezingReviewer

pytestmark = [
    pytest.mark.gui,
    pytest.mark.skipif(
        not os.environ.get("DISPLAY"),
        reason="GUI tests require an X display ($DISPLAY)",
    ),
]


class TestFreezingReviewer:
    """Smoke tests for the tkinter-based reviewer GUI."""

    def test_instantiation_loads_data_and_images(self, sgp_test_folder) -> None:
        """
        Given: SGP 2.21.24 base/ which has reviewed .dat + dat_Images/
        When:  FreezingReviewer is constructed.
        Then:  self.data is a non-empty DataFrame; self.images list non-empty.

        Real data: tests/test_data/SGP 2.21.24 base/
        """
        # TODO: window = tk.Tk(); window.withdraw()
        # TODO: app = FreezingReviewer(window, sgp_test_folder, 6, 32, dict_a,
        #                              includes=("reviewed",))
        # TODO: assert len(app.data) > 0; assert len(app.images) > 0
        # TODO: window.destroy()
        pytest.skip("not implemented")

    def test_update_image_increments_sample(self, sgp_test_folder) -> None:
        """
        Given: instantiated reviewer at image index 0.
        When:  _update_image(sample_idx=0, delta=+1) is called.
        Then:  data['Sample_0'][current_row] increases by 1 (clamped at
               wells_per_sample); 'changes' column records the audit.
        """
        pytest.skip("not implemented")

    def test_update_image_clamps_at_wells_per_sample(self, sgp_test_folder) -> None:
        """+1 beyond wells_per_sample is a no-op (or clamped)."""
        pytest.skip("not implemented")

    def test_update_image_negative_propagates_back(self, sgp_test_folder) -> None:
        """
        Given: a sample where well N first 'froze' at image index K.
        When:  -1 is pressed at index M > K.
        Then:  Sample_X[K..M] all decremented (monotonicity preserved).

        Source: button_handler.py monotonicity logic.
        """
        pytest.skip("not implemented")

    def test_changes_column_audit_trail(self, sgp_test_folder) -> None:
        """Every +1/-1 click appends a tuple (sample_idx, delta, row_idx) to 'changes'."""
        pytest.skip("not implemented")
