import tkinter as tk
from pathlib import Path

import pandas as pd

from olaf.CONSTANTS import NUM_SAMPLES
from olaf.utils.path_utils import natural_sort_key


class DataLoader:
    def __init__(self, root: tk.Tk, folder_path: Path) -> None:
        """
        Class to initialize the gui and load data and images for button handling.
        Args:
            root: tkinter root object
            folder_path: path to the project folder containing the images and .dat file
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

    def get_data_file(
        self, suffix: str = ".dat", excludes: list[str] = None
    ) -> tuple[Path, pd.DataFrame]:
        """
        Load a file with a given suffix (default: .dat) from the Project folder.
        Arguments to exclude files can be passed as a list to the "excludes" parameter.
        Because of pandas loading, the Date and Time in column "Time" are split in two
        Different columns and renamed to Date and Time respectively.
        It also adds a column to capture changes to the number of frozen wells.
        The function returns the file path and the data as a pandas DataFrame.
        Args:
            suffix: suffix of the file to load (default: .dat)
            excludes: combination of strings to exclude from the file name (default: "reviewed")

        Returns:
            tuple with the file path and the data as a pandas DataFrame
        """

        if excludes is None:
            excludes = ["reviewed"]
        data_file, data = Path(), pd.DataFrame()
        for file in self.folder_path.iterdir():
            if file.suffix == suffix and not any(excl in file.name for excl in excludes):
                data_file = file
                data = pd.read_csv(data_file, sep="\t", parse_dates=["Time"])
                # Give both date and time proper column names if they are split
                if "Time" in data.columns and "Unnamed: 1" in data.columns:
                    data.rename(columns={"Time": "Date", "Unnamed: 1": "Time"}, inplace=True)
                # Add a column to capture changes to the number of frozen wells
                data["changes"] = [[0] * NUM_SAMPLES for _ in range(len(data))]
                break
        if data.empty or data_file.name == "":
            raise FileNotFoundError("No .dat file found in the folder")

        return data_file, data

    def load_photos(self) -> list:
        """
        Load the images from the folder and sort them naturally and returns them in a list.
        Returns:
            list of pathlib.Path objects of the images
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
        Save the data to a new file with the prefix "reviewed_" added to the name.
        Returns:
            None, saves the data to a new  file
        """
        new_save_name = self.data_file.parent / f"reviewed_{self.data_file.name}"
        counter = 1
        # If the file already exists, add a number to the name
        while new_save_name.exists():
            new_file_name = f"reviewed_{self.data_file.stem}({counter}){self.data_file.suffix}"
            new_save_name = self.data_file.parent / new_file_name
            counter += 1
        self.data.to_csv(new_save_name, sep="\t", index=False)
        return
