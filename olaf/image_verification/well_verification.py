from freezing_reviewer import FreezingReviewer
import tkinter as tk
from pathlib2 import Path


if __name__ == "__main__":
    test_folder = Path.cwd().parent.parent / "tests" / "test_data" / "SGP 2.21.24 base"
    window = tk.Tk()
    app = FreezingReviewer(window, test_folder)
    window.mainloop()