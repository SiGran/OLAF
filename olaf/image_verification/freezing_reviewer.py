import tkinter as tk
from pathlib import Path

from olaf.utils.type_utils import ensure_list

from .button_handler import ButtonHandler


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
        Display the number of frozen wells for each sample in the current image.
        Args:
             current_index: index in the dataframe corresponding to the current image.

        Returns:
             None
        """
        current_temp = self.data.loc[current_index, "Avg_Temp"]
        temp_text = f"Current Temp (C)"
        temp_frame = tk.LabelFrame(self.root,text=temp_text)
        temp_frame.place(relx=0.5, y=30, anchor=tk.CENTER)
        label = tk.Label(temp_frame, text=str(current_temp))
        label.pack(padx=10, pady=5)
        return
