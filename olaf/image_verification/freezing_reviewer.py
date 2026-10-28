import tkinter as tk
from collections.abc import Sequence
from pathlib import Path

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
    shows the current count the correction is refused (it would make the count drop as
    temperature decreases).
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

        # Apply change to current and later; keep the value between 0 and max wells_per_sample
        if change < 0:  # go back to where this last went up, after the previous image
            # Check if the change would go below 0
            if self.data.loc[current_index:, f"Sample_{sample}"].values[0] + change < 0:
                print("Cannot decrease below 0!!")
                return
            # Work in row positions so this doesn't depend on the index being a RangeIndex
            pictures = self.data["Picture"].tolist()
            counts = self.data[f"Sample_{sample}"].tolist()
            current_row = pictures.index(picture_name)
            prev_row = previous_image_row(
                pictures, [p.name for p in self.photos], self.current_photo_index
            )
            start_row = minus_one_start_row(counts, current_row, prev_row)
            if start_row is None:
                print(
                    f"Sample {sample} was already {counts[current_row]} at the previous image; "
                    "go back and correct it there."
                )
                return
            current_index = self.data.index[start_row]

        self.data.loc[current_index:, f"Sample_{sample}"] += change
        self.data.loc[current_index:, f"Sample_{sample}"] = self.data.loc[
            current_index:, f"Sample_{sample}"
        ].clip(0, self.wells_per_sample)

        # Update the changes column with the change
        # bug can occur that turns the "changes" column into a string
        self.data["changes"] = self.data["changes"].apply(ensure_list)
        # Update the change from the click to the changes column
        self.data.loc[current_index:, "changes"] = self.data.loc[current_index:, "changes"].apply(
            lambda x: [int(y) + change if i == sample else y for i, y in enumerate(x)]
        )
        # NOTE: above line/column isn't corrected for clipping to (0, wells_per_sample)
        self._display_num_frozen(picture_name)
        return

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
