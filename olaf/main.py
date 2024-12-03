import tkinter as tk
from pathlib import Path

from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.processing.spaced_temp_csv import SpacedTempCSV

test_folder = Path.cwd().parent / "tests" / "test_data" / "SGP 2.21.24 base"
num_samples = 6
vol_air_filt = 10754  # L
wells_per_sample = 32
filter_used = 1.0  # between 0 and 1.0
vol_susp = 10  # mL
dict_samples_to_dilution = {
    "Sample_5": 1,
    "Sample_4": 11,
    "Sample_3": 121,
    "Sample_2": 1331,
    "Sample_1": 14641,
    "Sample_0": float("inf"),
}

if __name__ == "__main__":
    # GUI
    window = tk.Tk()
    app = FreezingReviewer(window, test_folder, num_samples)
    window.mainloop()
    # Processing to create .csv file
    spaced_temp_csv = SpacedTempCSV(test_folder, num_samples)
    spaced_temp_csv.create_temp_csv()
    # Processing to create INPs/L
    graph_data_csv = GraphDataCSV(
        test_folder,
        num_samples,
        vol_air_filt,
        wells_per_sample,
        filter_used,
        vol_susp,
        dict_samples_to_dilution,
    )
    graph_data_csv.convert_INPs_L()
