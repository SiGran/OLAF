import tkinter as tk
from pathlib import Path

from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.spaced_temp_csv import SpacedTempCSV

if __name__ == "__main__":
    # GUI
    test_folder = Path.cwd().parent / "tests" / "test_data" / "SGP 2.21.24 base"
    window = tk.Tk()
    app = FreezingReviewer(window, test_folder)
    window.mainloop()
    # Processing to create .csv file
    spaced_temp_csv = SpacedTempCSV(test_folder)
    spaced_temp_csv.create_temp_csv()
