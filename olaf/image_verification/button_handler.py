import tkinter as tk
from pathlib import Path

from ..CONSTANTS import NUM_SAMPLES
from .data_loader import DataLoader


class ButtonHandler(DataLoader):
    def __init__(self, root: tk.Tk, folder_path: Path) -> None:
        """
        Class to handle the buttons for the gui to review well freezing images.
        Args:
            root: tkinter root object
            folder_path: folder path to the project folder containing the images and .dat file
        """
        super().__init__(root, folder_path)
        self.photo_image_ref, self.back_button = tk.PhotoImage(), tk.Button()
        self.create_buttons()
        self.show_photo()
        return

    def create_buttons(self) -> None:
        """
        Create buttons for each sample to increase or decrease the number of frozen wells
        Returns:
            None
        """
        for i in range(NUM_SAMPLES):
            sample_frame = tk.LabelFrame(self.button_frame, text=f"sample_{i}")
            sample_frame.pack(side=tk.LEFT, padx=5)
            # lambda functions are used to pass the current value of i to the function
            min_button = tk.Button(
                sample_frame,
                text="-1",
                command=lambda j=i: self._update_image(j, -1),  # type: ignore
            )
            min_button.pack(side=tk.LEFT)

            plus_button = tk.Button(
                sample_frame,
                text="+1",
                command=lambda j=i: self._update_image(j, 1),  # type: ignore
            )
            plus_button.pack(side=tk.LEFT)
            # Add navigation buttons in the middle
            if i == (NUM_SAMPLES // 2) - 1:
                nav_frame = tk.Frame(self.button_frame)
                nav_frame.pack(side=tk.LEFT, padx=2)

                self.back_button = tk.Button(
                    nav_frame, text="Back", command=lambda: self._prev_image()
                )
                self.back_button.pack(side=tk.BOTTOM)
                self.back_button.config(state=tk.DISABLED)  # Initially disabled

                good_button = tk.Button(
                    nav_frame,
                    text="Good",
                    command=lambda: self._next_image(),
                )
                good_button.pack(side=tk.TOP)
        return

    def show_photo(self) -> None:
        """
        Function to display the current photo in the window and update the title with
        image name. This function is called when the window is first created and when
        the user navigates to the next or previous image.
        Returns:
            None
        """
        if self.photos:
            # Enable or disable the "Back" button based on the current photo index
            if self.current_photo_index == 0:
                self.back_button.config(state=tk.DISABLED)
            else:
                self.back_button.config(state=tk.NORMAL)
            photo_path = self.photos[self.current_photo_index]
            self.photo_image_ref = tk.PhotoImage(file=str(photo_path)).subsample(2)
            self.label.config(image=self.photo_image_ref)

            # Update the window title with the current image name
            self.root.title(f"Well Freezing Reviewer - {photo_path.name}")

            # Display num of frozen wells from the data
            self._display_num_frozen(photo_path.name)
        else:
            self.label.config(text="No images found")
        return

    def _update_image(self, sample: int, change: int) -> None:
        """
        (Placeholder to) Update the number of frozen wells for the current image
        Args:
            sample: which sample (column) to update, -1 for "Good"
            change: by what amount to change the sample frozen well value,
            -1 for decrease, 1 for increase.

        Returns:
            None
        """
        pass
        return

    def _next_image(self):
        """
        Go to the next photo in the list. If there are no more photos, call the closing
        sequence. Otherwise, show the next photo.
        Returns:
            None
        """
        self.current_photo_index += 1
        if self.current_photo_index >= len(self.photos):
            self.closing_sequence()
            self.root.quit()
        else:
            self.show_photo()
        return

    def _prev_image(self) -> None:
        """
        Go to the previous photo in the list. If there are no photos to go back to,
        do nothing.
        Returns:
            None
        """
        if self.current_photo_index > 0:
            self.current_photo_index -= 1
            self.show_photo()
        return

    def _display_num_frozen(self, pic_file_name: str) -> None:
        """
        (Placeholder to) Display the number of frozen wells for each sample in the
        current image.
        Args:
            pic_file_name: name of the current image being rendered.

        Returns:
            None
        """
        return

    def closing_sequence(self) -> None:
        """
        This function is automatically ran after the last image is reviewed and the
        GUI closes.
        Currently, it calls the save_data function from the DataLoader class.
        Returns:
            None
        """
        self.save_to_new_file()
        return
