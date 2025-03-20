import tkinter as tk
from pathlib import Path

from .button_handler import ButtonHandler


class FreezingReviewer(ButtonHandler):
    # TODO: Full screen makes it become weird ---> mainly location of the "Sample x" on top
    def __init__(self, root: tk.Tk, folder_path: Path, num_samples: int, includes: tuple) -> None:
        """
        Class that creates a GUI for reviewing well freezing images and
        updating the number of frozen wells.
        Class inherits from ButtonHandler and DataLoader.
        Args:
            root: tkinter root object
            folder_path: path to the project folder containing the images and .dat file
        """
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

        # Apply change to current and later, but keep the value between 0 and 32
        if change < 0:  # go back to were this went last up
            # Check if the change would go below 0
            if self.data.loc[current_index:, f"Sample_{sample}"].values[0] + change < 0:
                print("Cannot decrease below 0!!")
                return
            # Go back from current index and find the first index were the
            # current value, we're trying to change, was reached
            current_val = self.data.loc[current_index, f"Sample_{sample}"]
            for i in range(current_index, 0, -1):
                if self.data.loc[i, f"Sample_{sample}"] == current_val - 1:
                    current_index = current_index - i
                    break

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
        Args:
            pic_file_name: name of the current image

        Returns:
            None
        """
        # Find the row in the data frame corresponding to the current image
        row = self.data[self.data["Picture"] == pic_file_name]
        # TODO: use dict_to_samples instead of num_samples
        """
        Still set out the outline with all the samples
        but then use the dictionary to see which ones we should be lookg int
        """
        if not row.empty:
            for i in range(self.num_samples):
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
