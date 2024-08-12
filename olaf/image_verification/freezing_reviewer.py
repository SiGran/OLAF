import tkinter as tk
from pathlib import Path

from ..CONSTANTS import NUM_SAMPLES
from .button_handler import ButtonHandler


class FreezingReviewer(ButtonHandler):
    # TODO: Full screen makes it become weird ---> mainly location of the "Sample x" on top
    def __init__(self, root: tk.Tk, folder_path: Path) -> None:
        """
        Create a GUI for reviewing well freezing images and
        updating the number of frozen wells.
        :param root: is the tkinter root object
        :param folder_path: Path to the folder containing the images and .dat file.
        """
        super().__init__(root, folder_path)
        return

    def _update_image(self, sample: int, change: int) -> None:
        """
        Update the number of frozen wells for the current image
        :param sample: which sample (column) to update, -1 for "Good"
        :param change: which direction to change the value, -1 for decrease, 1 for
         increase.
        :return:
        """
        picture_name = self.photos[self.current_photo_index].name

        # Get the index of the current image in the data frame
        current_index = self.data.index[self.data["Picture"] == picture_name].tolist()[0]

        # Apply change to current and later, but keep the value between 0 and 32
        self.data.loc[current_index:, f"Sample_{sample}"] += change
        self.data.loc[current_index:, f"Sample_{sample}"] = self.data.loc[
            current_index:, f"Sample_{sample}"
        ].clip(0, 32)

        # Update the changes column with the change
        self.data.loc[current_index:, "changes"] = self.data.loc[current_index:, "changes"].apply(
            lambda x: [y + change if i == sample else y for i, y in enumerate(x)]
        )
        # NOTE: above line/column isn't corrected for clipping to (0, 32)
        self._display_num_frozen(picture_name)
        return

    def _display_num_frozen(self, pic_file_name: str) -> None:
        """
        Display the number of frozen wells for each sample in the current image.
        :param pic_file_name: name of the current image being rendered.
        :return:
        """
        # Find the row in the data frame corresponding to the current image
        row = self.data[self.data["Picture"] == pic_file_name]
        if not row.empty:
            for i in range(NUM_SAMPLES):
                value = row[f"Sample_{i}"].values[0]
                sample_frame = tk.LabelFrame(self.root, text=f"sample {i}")
                x_coord = (i + 1.2) * 100
                if i > 2:
                    x_coord += 100
                sample_frame.place(x=x_coord, y=170)  # Adjust x and y for proper spacing
                label = tk.Label(sample_frame, text=str(value))
                label.pack()
        else:
            print(f"Error: No data found for {pic_file_name}")
        return
