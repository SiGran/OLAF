"""
Tests for the pure helpers behind the GUI "-1" button in
olaf.image_verification.freezing_reviewer, so these run headless (no gui marker).

A -1 applies from the row where the count last rose to its current value. The previous
image is assumed checked and correct: if it already shows the current count, the -1 is
refused (returns None) rather than making the count drop as temperature decreases.
"""

from __future__ import annotations

import numpy as np

from olaf.image_verification.freezing_reviewer import (
    apply_minus_one,
    minus_one_start_row,
    previous_image_row,
    tally_change,
)


def _run() -> list[int]:
    """Toy run: wells freeze at rows 20, 50 and 80; 100 rows total."""
    return [0] * 20 + [1] * 30 + [2] * 30 + [3] * 20


class TestMinusOneStartRow:
    def test_undoes_rise_between_images(self) -> None:
        """
        Given: previous image at row 70 (count 2), -1 at row 90 (count 3), rise at row 80.
        Then:  the correction starts at the rise, so row 70 keeps its count.
        Regression: the old code returned 90 - 79 = 11 and wiped early freezing events.
        """
        assert minus_one_start_row(_run(), current_row=90, prev_row=70) == 80

    def test_rise_on_current_row(self) -> None:
        """The count rose exactly at the current row: only that row onwards changes."""
        assert minus_one_start_row(_run(), current_row=80, prev_row=70) == 80

    def test_rise_right_after_previous_image(self) -> None:
        """The rise is on the row straight after the previous image."""
        assert minus_one_start_row(_run(), current_row=90, prev_row=79) == 80

    def test_refused_when_previous_image_has_same_count(self) -> None:
        """
        Given: previous image at row 85 already shows 3, the same as the current image.
        Then:  None (refused); decrementing from row 86 would make the count drop
               with temperature.
        """
        assert minus_one_start_row(_run(), current_row=90, prev_row=85) is None

    def test_first_image_walks_back_to_row_zero(self) -> None:
        """With no previous image, the walk can reach and include row 0."""
        assert minus_one_start_row([1, 1, 1, 1], current_row=3, prev_row=None) == 0
        assert minus_one_start_row([0, 1, 1, 1], current_row=3, prev_row=None) == 1

    def test_noisy_higher_reading_does_not_stop_walk(self) -> None:
        """A transient higher count between rows doesn't end the walk early."""
        counts = [0, 0, 1, 2, 1, 1]
        assert minus_one_start_row(counts, current_row=5, prev_row=0) == 2


class TestPreviousImageRow:
    def test_finds_row_of_previous_image(self) -> None:
        pictures = [None, "a.png", None, "b.png", None, "c.png"]
        assert previous_image_row(pictures, ["a.png", "b.png", "c.png"], 2) == 3

    def test_first_image_has_no_previous(self) -> None:
        assert previous_image_row(["a.png", "b.png"], ["a.png", "b.png"], 0) is None

    def test_skips_images_missing_from_data(self) -> None:
        """An earlier image with no row is skipped in favour of the nearest one that has one."""
        pictures = ["a.png", None, "c.png"]
        assert previous_image_row(pictures, ["a.png", "b.png", "c.png"], 2) == 0

    def test_no_earlier_image_in_data(self) -> None:
        assert previous_image_row([None, "c.png"], ["a.png", "b.png", "c.png"], 2) is None


class TestTallyChange:
    def test_plus_and_minus_are_kept_apart(self) -> None:
        """+1 +1 +1 -1 gives (3, -1), not the net 2."""
        entry: tuple[int, int] = (0, 0)
        for change in (1, 1, 1, -1):
            entry = tally_change(entry, change)
        assert entry == (3, -1)

    def test_old_net_number_counts_as_all_plus_or_all_minus(self) -> None:
        """Files reviewed before the split store one net number per sample."""
        assert tally_change(2, -1) == (2, -1)
        assert tally_change(-3, 1) == (1, -3)
        assert tally_change(0, 1) == (1, 0)

    def test_numpy_numbers_and_lists_are_accepted(self) -> None:
        """Row deltas come from pandas as numpy ints; reloaded tallies can be lists."""
        assert tally_change(np.int64(2), np.int64(-1)) == (2, -1)
        assert tally_change([1, 0], 1) == (2, 0)
        assert tally_change((1, -1), 0) == (1, -1)


class TestApplyMinusOne:
    def test_without_hidden_wells_undoes_the_rise(self) -> None:
        """Below the cap this is the plain -1 from the rise on."""
        assert apply_minus_one([0, 1, 1, 2, 2], cap=4, start_row=3, current_row=4) == [
            0,
            1,
            1,
            1,
            1,
        ]

    def test_hidden_surplus_at_current_is_dropped_in_one_click(self) -> None:
        """
        Given: current row shows 4 (cap) with 2 hidden on top (6); a later row has 1 more.
        Then:  current shows 3; the later row keeps its extra well (4).
        """
        assert apply_minus_one([3, 4, 6, 7], cap=4, start_row=1, current_row=2) == [3, 3, 3, 4]

    def test_rows_between_rise_and_current_end_one_below_the_cap(self) -> None:
        """Rows from the rise up to the current image show one less, never below the
        previous image (row 0, showing 3)."""
        assert apply_minus_one([3, 4, 4, 6], cap=4, start_row=1, current_row=3) == [3, 3, 3, 3]

    def test_later_noisy_row_hidden_by_the_cap_drops_at_most_one(self) -> None:
        """
        Given: uncapped 0, 3, 5, 4, 5 (shown 0, 3, 4, 4, 4); row 3 is a noisy dip hidden by the cap.
        Then:  a -1 on row 2 shows 0, 3, 3, 3, 3, not 0, 3, 3, 2, 3.
        """
        assert apply_minus_one([0, 3, 5, 4, 5], cap=4, start_row=2, current_row=2) == [
            0,
            3,
            3,
            3,
            3,
        ]

    def test_never_below_zero(self) -> None:
        assert apply_minus_one([0, 1, 1], cap=4, start_row=1, current_row=2) == [0, 0, 0]
