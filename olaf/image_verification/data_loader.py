import tkinter as tk
from pathlib import Path

import pandas as pd

from olaf.utils.path_utils import natural_sort_key

from ..CONSTANTS import NUM_SAMPLES


class DataLoader:
    def __init__(self, root: tk.Tk, folder_path: Path) -> None:
        """
        Class to initialize the gui and load data and images for button handling.
        :param root: is the tkinter root object
        :param folder_path: Path to the folder containing the images and .dat file.
        """
        self.root = root
        self.folder_path = folder_path
        self.data_file, self.data = self.get_data_file()

        # Set up the window
        self.root.title("Well Freezing Reviewer")
        self.label = tk.Label(root)
        self.label.pack()

        # Load the images
        self.current_photo_index = 0
        self.photos = self.load_photos()

        # Set up the buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        return

    def get_data_file(self) -> tuple[Path, pd.DataFrame]:
        """
        Find the .dat file in the folder and load it into a pandas DataFrame
        :return:
        """
        data_file, data = Path(), pd.DataFrame()
        for file in self.folder_path.iterdir():
            if file.suffix == ".dat" and "reviewed" not in file.name:
                data_file = file
                data = pd.read_csv(data_file, sep="\t", parse_dates=["Time"])
                # Give both date and time proper column names
                data.rename(columns={"Time": "Date", "Unnamed: 1": "Time"}, inplace=True)
                # Add a column to capture changes to the number of frozen wells
                data["changes"] = [[0] * NUM_SAMPLES for _ in range(len(data))]
                break
        if data.empty or data_file.name == "":
            raise FileNotFoundError("No .dat file found in the folder")

        return data_file, data

    def load_photos(self) -> list:
        """
        Load all images in the "dat_Images" folder into a list.
        :return:
        """
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

    def save_data(self) -> None:
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
