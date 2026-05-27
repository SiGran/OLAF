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


def _tk_available() -> bool:
    """Return True only if tkinter can actually open a window.

    tkinter aborts the whole process (SIGABRT) when $DISPLAY is set but no X
    server is reachable, so a normal try/except can't guard it. Run the probe
    in a subprocess so a crash there doesn't kill pytest.
    """
    if not os.environ.get("DISPLAY"):
        return False
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-c", "import tkinter; r=tkinter.Tk(); tkinter.Label(r); r.destroy()"],
            timeout=5,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


pytestmark = [
    pytest.mark.gui,
    pytest.mark.skipif(
        not _tk_available(),
        reason="GUI tests require a usable X display ($DISPLAY + X server)",
    ),
]


@pytest.fixture
def reviewer(sgp_golden_folder, sample_dilution_dict_a):
    """Build a FreezingReviewer against the SGP golden folder.

    Skips when the dat_images/ directory is missing. Yields the app and tears
    down the tk root afterwards.
    """
    images_dir = sgp_golden_folder / "dat_images"
    if not images_dir.exists():
        pytest.skip(f"Real fixture missing: {images_dir}")

    import tkinter as tk

    from olaf.image_verification.freezing_reviewer import FreezingReviewer

    window = tk.Tk()
    window.withdraw()
    try:
        app = FreezingReviewer(
            window,
            sgp_golden_folder,
            6,
            32,
            sample_dilution_dict_a,
            includes=("reviewed",),
        )
        # The committed reviewed.dat has an empty Picture column.
        # Assign loaded photo names to the first N rows so _update_image can
        # locate the "current image" row via Picture lookup.
        for idx, photo in enumerate(app.photos):
            if idx < len(app.data):
                app.data.loc[idx, "Picture"] = photo.name
        yield app
    finally:
        window.destroy()


class TestFreezingReviewer:
    """Smoke tests for the tkinter-based reviewer GUI."""

    def test_instantiation_loads_data_and_images(self, reviewer) -> None:
        """
        Given: SGP golden folder with reviewed.dat + dat_images/
        When:  FreezingReviewer is constructed.
        Then:  self.data is a non-empty DataFrame; self.photos list non-empty.
        """
        assert len(reviewer.data) > 0
        assert len(reviewer.photos) > 0
        # All photos are pathlib.Path objects pointing at images
        assert all(p.suffix.lower() in (".png", ".jpg", ".jpeg") for p in reviewer.photos)
        # Natural sort: Image_1, Image_2, Image_10 (NOT lexical 1, 10, 2)
        names = [p.name for p in reviewer.photos]
        assert names.index("Image_2.png") < names.index("Image_10.png")

    def test_update_image_increments_sample(self, reviewer) -> None:
        """
        Given: instantiated reviewer at image index 0.
        When:  _update_image(sample=0, change=+1) is called.
        Then:  data['Sample_0'][current_row:] increases by 1.
        """
        reviewer.current_photo_index = 0
        current_idx = reviewer.data.index[
            reviewer.data["Picture"] == reviewer.photos[0].name
        ].tolist()[0]
        before = reviewer.data.loc[current_idx, "Sample_0"]
        reviewer._update_image(sample=0, change=1)
        after = reviewer.data.loc[current_idx, "Sample_0"]
        assert after == before + 1
        # The increment propagates forward
        assert (
            reviewer.data.loc[current_idx:, "Sample_0"] >= before + 1
        ).all() or reviewer.data.loc[current_idx:, "Sample_0"].max() <= reviewer.wells_per_sample

    def test_update_image_clamps_at_wells_per_sample(self, reviewer) -> None:
        """+1 beyond wells_per_sample is clamped (no overflow)."""
        reviewer.current_photo_index = 0
        current_idx = reviewer.data.index[
            reviewer.data["Picture"] == reviewer.photos[0].name
        ].tolist()[0]
        # Pre-set Sample_0 at and after current_idx to the max
        reviewer.data.loc[current_idx:, "Sample_0"] = reviewer.wells_per_sample
        reviewer._update_image(sample=0, change=1)
        assert (reviewer.data.loc[current_idx:, "Sample_0"] <= reviewer.wells_per_sample).all()
        assert reviewer.data.loc[current_idx, "Sample_0"] == reviewer.wells_per_sample

    def test_update_image_negative_clamps_at_zero(self, reviewer) -> None:
        """-1 from 0 is a no-op and prints a warning instead of going negative."""
        reviewer.current_photo_index = 0
        current_idx = reviewer.data.index[
            reviewer.data["Picture"] == reviewer.photos[0].name
        ].tolist()[0]
        # Sample_0 is already 0 in the fixture
        reviewer.data.loc[current_idx:, "Sample_0"] = 0
        reviewer._update_image(sample=0, change=-1)
        # All values remain non-negative
        assert (reviewer.data.loc[current_idx:, "Sample_0"] >= 0).all()

    def test_changes_column_audit_trail(self, reviewer) -> None:
        """A +1 click records a non-zero delta in the 'changes' column at the current row."""
        reviewer.current_photo_index = 0
        current_idx = reviewer.data.index[
            reviewer.data["Picture"] == reviewer.photos[0].name
        ].tolist()[0]
        reviewer._update_image(sample=0, change=1)
        change_row = reviewer.data.loc[current_idx, "changes"]
        # changes column is a list-like of per-sample deltas
        from olaf.utils.type_utils import ensure_list

        deltas = ensure_list(change_row)
        assert deltas[0] == 1
