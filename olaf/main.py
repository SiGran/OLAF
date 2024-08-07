import tkinter as tk
from pathlib import Path

from olaf.image_verification.freezing_reviewer import FreezingReviewer

if __name__ == "__main__":
    test_folder = Path.cwd().parent / "tests" / "test_data" / "SGP 2.21.24 base"
    window = tk.Tk()
    app = FreezingReviewer(window, test_folder)
    window.mainloop()
