import tkinter as tk
from pathlib import Path

from olaf.utils.data_handler import DataHandler
from olaf.utils.path_utils import natural_sort_key


class DataLoader(DataHandler):
    def __init__(
        self, root: tk.Tk, folder_path: Path, includes: list[str] = None, excludes: list[str] = None
    ) -> None:
        """
        Class to initialize the gui and load data and images for button handling.
        Args:
            root: tkinter root object
            folder_path: path to the project folder containing the images and .dat file
        """
        if excludes is None:
            excludes = ["reviewed"]
        if includes is None:
            includes = ["base"]
        super().__init__(folder_path, includes=includes, excludes=excludes)
        self.root = root

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
