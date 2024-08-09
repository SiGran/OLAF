import tkinter as tk
from pathlib import Path

import pandas as pd

from olaf.utils.path_utils import natural_sort_key

NUM_SAMPLES = 6


class FreezingReviewer:
    # TODO: how would you create going back button?
    # TODO: Full screen makes it become weird. Why? And fix?
    def __init__(self, root: tk.Tk, folder_path: Path) -> None:
        """
        Create a GUI for reviewing well freezing images and
        updating the number of frozen wells.
        :param root: is the tkinter root object
        :param folder_path: Path to the folder containing the images and .dat file.
        """
        self.root = root
        self.folder_path = folder_path
        self.data_file, self.data = self._get_data_file()

        # Set up the window
        self.root.title("Well Freezing Reviewer")
        self.label = tk.Label(root)
        self.label.pack()

        # Set up the buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        self.sample_buttons = self._create_buttons()

        # Set up the photo viewer
        self.current_photo_index = 0
        self.photos = self._load_photos()
        self._show_photo()
        return

    def _get_data_file(self) -> tuple[Path, pd.DataFrame]:
        """
        Find the .dat file in the folder and load it into a pandas DataFrame
        :return:
        """
        data_file, data = Path(), pd.DataFrame()
        for file in self.folder_path.iterdir():
            if file.suffix == ".dat" and "reviewed" not in file.name:
                data_file = file
                # TODO: Why is there a tab between the date and time in the date/time column?
                data = pd.read_csv(data_file, sep="\t", parse_dates=["Time"])
                # Give both date and time proper column names
                data.rename(columns={"Time": "Date", "Unnamed: 1": "Time"}, inplace=True)
                # Add a column to capture changes to the number of frozen wells
                data["changes"] = [[0] * NUM_SAMPLES for _ in range(len(data))]
                break
        if data.empty or data_file.name == "":
            raise FileNotFoundError("No .dat file found in the folder")

        return data_file, data

    def _create_buttons(self) -> list:
        """
        Create buttons for each sample to increase or decrease the number of frozen wells
        :return:
        """
        sample_buttons = []
        for i in range(NUM_SAMPLES):
            sample_frame = tk.LabelFrame(self.button_frame, text=f"sample_{i}")
            sample_frame.pack(side=tk.LEFT, padx=5, pady=5)
            # lambda functions are used to pass the current value of i to the function
            min_button = tk.Button(
                sample_frame,
                text="-1",
                command=lambda j=i: self._update_frozen_wells(j, -1),  # type: ignore
            )
            min_button.pack(side=tk.LEFT)
            sample_buttons.append(min_button)

            plus_button = tk.Button(
                sample_frame,
                text="+1",
                command=lambda j=i: self._update_frozen_wells(j, 1),  # type: ignore
            )
            plus_button.pack(side=tk.LEFT)
            sample_buttons.append(plus_button)
            # Add a "Good" button in the middle
            if i == (NUM_SAMPLES // 2) - 1:
                good_button = tk.Button(
                    self.button_frame,
                    text="Good",
                    command=lambda: self._update_frozen_wells(-1, 0),
                )
                good_button.pack(side=tk.LEFT)
                sample_buttons.append(good_button)
        return sample_buttons

    def _load_photos(self) -> list:
        """
        Load all images in the "dat_Images" folder into a list.
        :return:
        """
        # TODO: add error if images not found
        images_folder = next(
            (
                folder
                for folder in self.folder_path.iterdir()
                if folder.is_dir() and folder.name.endswith("Images")
            ),
            None,
        )
        if images_folder:
            if images_folder.is_dir():
                files = [
                    file
                    for file in images_folder.iterdir()
                    if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".bmp")
                ]
                # lambda function to sort pathlib paths naturally
                photos = sorted(files, key=lambda x: natural_sort_key(str(x)))
            else:
                raise NotADirectoryError(f"images folder ({images_folder}) is not a directory")
        else:
            raise FileNotFoundError("No images folder found in the folder")
        return photos

    def _show_photo(self) -> None:
        """
        Display the current photo in the window and update the title with image name.
        :return:
        """
        if self.photos:
            photo_path = self.photos[self.current_photo_index]
            self.photo_image_ref = tk.PhotoImage(file=str(photo_path))
            self.photo_image_ref = self.photo_image_ref.subsample(2)
            self.label.config(image=self.photo_image_ref)

            # Update the window title with the current image name
            self.root.title(f"Well Freezing Reviewer - {photo_path.name}")

            # Display sample values
            self._display_num_frozen(photo_path.name)
        else:
            self.label.config(text="No images found")
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

    def _update_frozen_wells(self, sample: int, change: int) -> None:
        """
        Update the number of frozen wells for the current image
        :param sample: which sample (column) to update, -1 for "Good"
        :param change: which direction to change the value, -1 for decrease, 1 for
         increase.
        :return:
        """
        if sample == -1 and change == 0:  # All good -> next image
            self.current_photo_index += 1
            if self.current_photo_index >= len(self.photos):
                self._save_data()
                self.root.quit()
            else:
                self._show_photo()
        else:  # Update the number of frozen wells for the clicked sample
            picture_name = self.photos[self.current_photo_index].name

            # Get the index of the current image in the data frame
            current_index = self.data.index[self.data["Picture"] == picture_name].tolist()[0]

            # Apply change to current and later, but keep the value between 0 and 32
            self.data.loc[current_index:, f"Sample_{sample}"] += change
            self.data.loc[current_index:, f"Sample_{sample}"] = self.data.loc[
                current_index:, f"Sample_{sample}"
            ].clip(0, 32)

            # Update the changes column with the change
            self.data.loc[current_index:, "changes"] = self.data.loc[
                current_index:, "changes"
            ].apply(lambda x: [y + change if i == sample else y for i, y in enumerate(x)])
            # TODO: above line doesn't correct for the clipping (0, 32)
            self._display_num_frozen(picture_name)
        return

    def _save_data(self) -> None:
        """
        Save the reviewed data to a new file with the prefix "reviewed_"
        :return:
        """
        new_save_name = self.data_file.parent / f"reviewed_{self.data_file.name}"
        counter = 0
        # If the file already exists, add a number to the name
        while new_save_name.exists():
            counter += 1
            if counter > 1:  # need to remove previous counter added to name
                new_file_name = f"{new_save_name.stem[0:-3]}({counter}).dat"
            else:
                new_file_name = f"{new_save_name.stem}({counter}).dat"
            new_save_name = new_save_name.parent / new_file_name
        self.data.to_csv(new_save_name, sep="\t", index=False)
        return
