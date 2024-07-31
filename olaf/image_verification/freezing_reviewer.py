import tkinter as tk
from pathlib2 import Path
import re
import pandas as pd


class FreezingReviewer:
    def __init__(self, root: tk.Tk, folder_path: Path):
        self.root = root
        self.images_folder = Path(folder_path) / "dat_Images"
        self.data = None
        self.dat_file = None

        for file in folder_path.iterdir():
            if file.suffix == ".dat":
                self.dat_file = file
                self.data = pd.read_csv(self.dat_file, sep="\t")
                break
        if not hasattr(self, "data"):
            raise FileNotFoundError("No .dat file found in the folder")

        self.root.title("Well Freezing Reviewer")

        self.label = tk.Label(root)
        self.label.pack()

        self.button_frame = tk.Frame(root)
        self.button_frame.pack()

        self.sample_buttons = []
        for i in range(6):
            sample_frame = tk.LabelFrame(self.button_frame, text=f"sample_{i}")
            sample_frame.pack(side=tk.LEFT, padx=5, pady=5)

            self.min_button = tk.Button(sample_frame, text="-1",
                                        command=lambda j=i: self.update_frozen(j, -1))
            self.min_button.pack(side=tk.LEFT)
            self.sample_buttons.append(self.min_button)

            self.plus_button = tk.Button(sample_frame, text="+1",
                                         command=lambda j=i: self.update_frozen(j, 1))
            self.plus_button.pack(side=tk.LEFT)
            self.sample_buttons.append(self.plus_button)
            if i == 2:
                self.good_button = tk.Button(self.button_frame, text="Good",
                                             command=lambda: self.update_frozen(-1, 0))
                self.good_button.pack(side=tk.LEFT)
                self.sample_buttons.append(self.good_button)

        self.photos = []
        self.current_photo_index = 0

        self.load_photos()

    def load_photos(self):
        if self.images_folder.exists():
            files = [file for file in self.images_folder.iterdir() if
                     file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp')]
            self.photos = sorted(files, key=lambda x: _natural_sort_key(str(x)))
            self.show_photo()

    def show_photo(self):
        if self.photos:
            photo_path = self.photos[self.current_photo_index]
            self.photo_image_ref = tk.PhotoImage(file=str(photo_path))
            self.photo_image_ref = self.photo_image_ref.subsample(2)
            self.label.config(image=self.photo_image_ref)

            # Update the window title with the current image name
            self.root.title(f"Well Freezing Reviewer - {photo_path.name}")

            # Display sample values
            self.display_sample_values(photo_path.name)

    def display_sample_values(self, pic_file_name):
        # Find the row in the data frame corresponding to the current image
        row = self.data[self.data['Picture'] == pic_file_name]
        if not row.empty:
            for i in range(6):
                value = row[f"Sample_{i}"].values[0]
                sample_frame = tk.LabelFrame(self.root, text=f"sample {i}")
                x_coord = (i + 1.2) * 100
                if i > 2:
                    x_coord += 100
                sample_frame.place(x=x_coord, y=170)  # Adjust x and y for proper spacing
                label = tk.Label(sample_frame, text=str(value))
                label.pack()

    def update_frozen(self, sample, change):
        if sample == -1 and change == 0:  # Only move to the next picture if "Good" is clicked
            self.current_photo_index = (self.current_photo_index + 1) % len(self.photos)
            self.show_photo()
        else:
            # Update the data frame with the new value
            picture_name = self.photos[self.current_photo_index].name
            current_index = self.data.index[self.data['Picture'] == picture_name].tolist()[0]
            self.data.loc[current_index:, f"Sample_{sample}"] += change
            # Add check to ensure values don't exceed 32
            self.data.loc[current_index:, f"Sample_{sample}"] = self.data.loc[current_index:, f"Sample_{sample}"].clip(0, 32)
            # Refresh the displayed sample values
            self.display_sample_values(picture_name)


def _natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in
            re.split(r'(\d+)', s)]