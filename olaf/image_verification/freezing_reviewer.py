import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from tkinter import messagebox

import pandas as pd

from olaf.utils.type_utils import ensure_list

from .button_handler import ButtonHandler


def previous_image_row(
    pictures: Sequence[object], photo_names: Sequence[str], photo_index: int
) -> int | None:
    """
    Find the row of the nearest earlier image that appears in the data.
    Args:
        pictures: the "Picture" column, positional by row
        photo_names: image file names in display order
        photo_index: index of the current image in photo_names

    Returns:
        Positional row of that image, or None if no earlier image is in the data
    """
    first_row: dict[object, int] = {}
    for row, picture in enumerate(pictures):
        first_row.setdefault(picture, row)
    for name in reversed(photo_names[:photo_index]):
        if name in first_row:
            return first_row[name]
    return None


def minus_one_start_row(
    counts: Sequence[int], current_row: int, prev_row: int | None
) -> int | None:
    """
    Find the first row a -1 correction applies to: the row where the count last rose to
    its current value. The previous image is assumed checked and correct, so if it already
    shows the current count there is no such row after it (the correction would make the
    count drop as temperature decreases); the caller asks the researcher what to do.
    Args:
        counts: frozen well counts of one sample, positional by row
        current_row: row of the image the correction is made on
        prev_row: row of the previous image, None if there is none

    Returns:
        First row to decrement, or None if the previous image already has this count
    """
    target = counts[current_row]
    if prev_row is not None and counts[prev_row] >= target:
        return None
    floor_row = 0 if prev_row is None else prev_row + 1
    row = current_row
    while row > floor_row and counts[row - 1] >= target:
        row -= 1
    return row


def apply_minus_one(
    uncapped: Sequence[int], cap: int, start_row: int, current_row: int
) -> list[int]:
    """
    New uncapped counts after a -1 that undoes the rise starting at start_row. The shown
    (capped) count on current_row drops by exactly 1, so a hidden surplus above the cap there
    is dropped too (e.g. 32 shown with 2 hidden on top goes to 31).
    Args:
        uncapped: running counts of one sample without the top cap, positional by row
        cap: wells_per_sample
        start_row: first row of the rise, from minus_one_start_row()
        current_row: row of the image the correction is made on

    Returns:
        Updated uncapped counts, never below 0
    """
    drop = uncapped[current_row] - min(uncapped[current_row], cap) + 1
    new = list(uncapped)
    # Rows between the rise and this image show one less, same as undoing the rise
    for row in range(start_row, current_row):
        new[row] = min(uncapped[row], cap) - 1
    # This image and later drop by the same amount, keeping surplus from later clicks, but
    # never show more than one less (a lower, noisy count hidden by the cap must not fall below)
    for row in range(current_row, len(new)):
        new[row] = max(uncapped[row] - drop, min(uncapped[row], cap) - 1)
    return [max(count, 0) for count in new]


def tally_change(entry: int | tuple[int, int] | list[int], change: int) -> tuple[int, int]:
    """
    Add a change to a sample's (plus, minus) tally in the "changes" column.
    Args:
        entry: current (plus, minus) tally; files reviewed before the split hold one net number,
            which counts as all plus or all minus
        change: the change to this row's count (0 just converts an old net number)

    Returns:
        Updated (plus, minus) tally
    """
    if not isinstance(entry, tuple | list):
        net = int(entry)
        entry = (max(net, 0), min(net, 0))
    plus, minus = (int(value) for value in entry)
    change = int(change)
    return plus + max(change, 0), minus + min(change, 0)


class FreezingReviewer(ButtonHandler):
    def __init__(
        self,
        root: tk.Tk,
        folder_path: Path,
        num_samples: int,
        wells_per_sample: int,
        dict_samples_to_dilution: dict,
        includes: tuple,
    ) -> None:
        """
        Class that creates a GUI for reviewing well freezing images and
        updating the number of frozen wells.
        Class inherited from ButtonHandler and DataLoader.
        Args:
            root: tkinter root object
            folder_path: path to the project folder containing the images and .dat file
        """
        self.dict_samples_to_dilution = dict_samples_to_dilution
        self.wells_per_sample = wells_per_sample
        # Per-sample frozen counts before capping at wells_per_sample, filled on first edit
        self._uncapped: dict[int, pd.Series] = {}
        # Initialize temperature display widget references
        self.temp_frame: tk.LabelFrame | None = None
        self.temp_label: tk.Label | None = None
        super().__init__(root, folder_path, num_samples, includes)
        return

    def _update_image(self, sample: int, change: int) -> None:
        """
        Update the number of frozen wells for the given sample in the current image.
        Args:
            sample: sample number to update
            change: change in the number of frozen wells

        Returns:
            None
        """
        picture_name = self.photos[self.current_photo_index].name

        # Get the index of the current image in the data frame
        current_index = self.data.index[self.data["Picture"] == picture_name].tolist()[0]

        # Show current temperature at top of GUI
        self._display_current_temp(current_index)

        # Work in row positions so this doesn't depend on the index being a RangeIndex
        col = f"Sample_{sample}"
        pictures = self.data["Picture"].tolist()
        shown = self.data[col].tolist()
        current_row = pictures.index(picture_name)
        # Keep a running count without the wells_per_sample cap and only cap what is shown/saved:
        # a +1 for a well the camera saw late is later cancelled by a -1, and capping in between
        # loses a well. Each click changes the shown count on this image by exactly 1
        uncapped = self._uncapped.setdefault(sample, self.data[col].copy())
        old = uncapped.tolist()

        if change > 0:  # apply from this image forward
            if shown[current_row] >= self.wells_per_sample:
                self._warn(
                    f"Sample {sample} is already full ({self.wells_per_sample}) at this image."
                )
                return
            new = old[:current_row] + [count + 1 for count in old[current_row:]]
        else:  # go back to where this last went up, after the previous image
            if shown[current_row] == 0:
                self._warn("Cannot decrease below 0!!")
                return
            prev_row = previous_image_row(
                pictures, [p.name for p in self.photos], self.current_photo_index
            )
            start_row = minus_one_start_row(shown, current_row, prev_row)
            if start_row is None:  # the previous image already shows this count
                start_row = self._resolve_minus_one_conflict(
                    sample, pictures, shown, current_row, prev_row
                )
                if start_row is None:
                    return
            new = apply_minus_one(old, self.wells_per_sample, start_row, current_row)

        uncapped[:] = new
        self.data[col] = uncapped.clip(0, self.wells_per_sample)

        # Update the changes column with what happened to each row
        # bug can occur that turns the "changes" column into a string
        self.data["changes"] = self.data["changes"].apply(ensure_list)
        # Add each row's change to its (plus, minus) tally for this sample; converting the
        # other samples too, so a row from an older file never mixes old numbers and tallies
        deltas = [n - o for n, o in zip(new, old, strict=True)]
        self.data["changes"] = [
            [tally_change(y, delta if i == sample else 0) for i, y in enumerate(x)] if delta else x
            for x, delta in zip(self.data["changes"], deltas, strict=True)
        ]
        # NOTE: like the uncapped count, this isn't clipped to (0, wells_per_sample)
        self._display_num_frozen(picture_name)
        return

    def _resolve_minus_one_conflict(
        self,
        sample: int,
        pictures: list,
        shown: list[int],
        current_row: int,
        prev_row: int | None,
    ) -> int | None:
        """
        The previous image already shows the count a -1 is clicked on. Ask whether to go to
        the image where the count rose, or to lower it from there anyway (which lowers the
        checked earlier image(s) too).
        Args:
            sample: sample number being corrected
            pictures: the "Picture" column, positional by row
            shown: shown counts of the sample, positional by row
            current_row: row of the current image
            prev_row: row of the previous image (always set when there is a conflict)

        Returns:
            Row to apply the -1 from, or None if nothing should change
        """
        if prev_row is None:  # a conflict needs a previous image; keep mypy happy
            return None
        # Walk back from the previous image (not the current one), so a noisy dip between the
        # two images doesn't put the rise after the previous image
        count = shown[current_row]
        rise_row = prev_row
        while rise_row > 0 and shown[rise_row - 1] >= count:
            rise_row -= 1
        # The first image at or after the rise is the first one showing this count
        first_row = {name: row for row, name in reversed(list(enumerate(pictures)))}
        goto_index = min(
            (i for i, p in enumerate(self.photos) if first_row.get(p.name, -1) >= rise_row),
            key=lambda i: first_row[self.photos[i].name],
        )
        goto_name = self.photos[goto_index].name
        prev_name = pictures[prev_row]
        choice = self._ask_minus_one_conflict(
            f"Sample {sample} was already {count} at the previous image ({prev_name}).\n"
            f"The count went up to {count} at {goto_name}.\n\n"
            f"Go there to correct it, or lower it from {goto_name} on anyway?",
            goto_name,
        )
        if choice == "goto":
            self.current_photo_index = goto_index
            self.show_photo()
            return None
        if choice == "proceed":
            return rise_row
        return None

    def _ask_minus_one_conflict(self, message: str, goto_name: str) -> str:
        """
        Pop-up for a -1 that conflicts with the previous image.
        Args:
            message: explanation shown in the pop-up
            goto_name: image the "Go to" button jumps to

        Returns:
            "goto", "proceed", or "cancel" if the pop-up was closed
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Previous image has the same count")
        dialog.transient(self.root)
        choice = tk.StringVar(value="cancel")

        def choose(value: str) -> None:
            choice.set(value)
            dialog.destroy()

        tk.Label(dialog, text=message, justify=tk.LEFT, wraplength=420).pack(padx=15, pady=10)
        buttons = tk.Frame(dialog)
        buttons.pack(pady=(0, 10))
        tk.Button(buttons, text=f"Go to {goto_name}", command=lambda: choose("goto")).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(
            buttons, text="Acknowledged, proceed anyway", command=lambda: choose("proceed")
        ).pack(side=tk.LEFT, padx=5)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return choice.get()

    def _warn(self, message: str) -> None:
        """Show a warning pop-up (a print is easy to miss while reviewing)."""
        messagebox.showwarning("Well Freezing Reviewer", message, parent=self.root)

    def _display_num_frozen(self, pic_file_name: str) -> None:
        """
        Display the number of frozen wells for each sample in the current image.
        Args:
            pic_file_name: name of the current image

        Returns:
            None
        """
        # Find the row in the data frame corresponding to the current image
        row = self.data[self.data["Picture"] == pic_file_name]

        # Clear any existing sample frames
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.LabelFrame) and "sample" in widget["text"]:
                widget.destroy()

        if not row.empty:
            # Use the includes parameter to determine which samples to display
            samples_to_display = range(self.num_samples)

            # Create a container frame to hold all sample frames
            container = tk.Frame(self.root)
            container.place(relx=0.5, y=100, anchor=tk.CENTER)

            for idx, i in enumerate(samples_to_display):
                value = row[f"Sample_{i}"].values[0]
                if f"Sample_{i}" in self.dict_samples_to_dilution:
                    frame_text = f"Sample {i} \n ({self.dict_samples_to_dilution[f'Sample_{i}']})"
                else:
                    frame_text = f"Sample {i} \n (Not in Dict)"
                sample_frame = tk.LabelFrame(container, text=frame_text)
                sample_frame.grid(row=0, column=idx, padx=20)
                label = tk.Label(sample_frame, text=str(value))
                label.pack(padx=10, pady=5)
        else:
            print(f"Error: No data found for {pic_file_name}")
        return

    def _display_current_temp(self, current_index: int) -> None:
        """
        Display the current temperature for the image.
        Args:
             current_index: index in the dataframe corresponding to the current image.

        Returns:
             None
        """
        current_temp = self.data.loc[current_index, "Avg_Temp"]

        # Create widgets only if they don't exist yet
        if self.temp_label is None:
            temp_text = "Current Temp (C)"
            self.temp_frame = tk.LabelFrame(self.root, text=temp_text)
            self.temp_frame.place(relx=0.5, y=30, anchor=tk.CENTER)
            self.temp_label = tk.Label(self.temp_frame, text=str(current_temp))
            self.temp_label.pack(padx=10, pady=5)
        else:
            self.temp_label.config(text=str(current_temp))
        return
