import tkinter as tk
from pathlib import Path

from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.processing.spaced_temp_csv import SpacedTempCSV

test_folder = Path.cwd().parent / "tests" / "test_data" / "SGP 3.28.24 base"
start_time = "2021-03-28 15:00:00"
end_time = "2021-03-28 16:00:00"
filter_color = "white"
"more adding hear?"
num_samples = 6
vol_air_filt = 10754  # L
wells_per_sample = 32
filter_used = 1.0  # between 0 and 1.0
vol_susp = 10  # mL
treatment = (
    "base",
    # "heat",
    # "peroxide",
    # "blank",
    # "blank heat",
    # "blank peroxide,"
)  # uncomment the one you want to use

# dict_samples_to_dilution = {
#     "Sample_5": 1,
#     "Sample_4": 11,
#     "Sample_3": 121,
#     "Sample_2": 1331,
#     "Sample_1": 14641,
#     "Sample_0": float("inf"),
# }
dict_samples_to_dilution = {
    "Sample_0": 1,
    "Sample_1": 11,
    "Sample_2": 121,
    "Sample_3": 1331,
    "Sample_4": 14641,
    "Sample_5": float("inf"),
}


if __name__ == "__main__":
    # GUI

    window = tk.Tk()
    app = FreezingReviewer(window, test_folder, num_samples, includes=treatment)
    window.mainloop()

    # # Processing to create .csv file
    spaced_temp_csv = SpacedTempCSV(test_folder, num_samples, includes=treatment)
    spaced_temp_csv.create_temp_csv(dict_samples_to_dilution)

    # Processing to create INPs/L
    graph_data_csv = GraphDataCSV(
        test_folder,
        num_samples,
        vol_air_filt,
        wells_per_sample,
        filter_used,
        vol_susp,
        dict_samples_to_dilution,
        includes=treatment,
    )
    graph_data_csv.convert_INPs_L()
