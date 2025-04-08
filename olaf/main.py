import re
import tkinter as tk
from pathlib import Path

from CONSTANTS import DATE_PATTERN

from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.processing.spaced_temp_csv import SpacedTempCSV

test_folder = (
    Path.cwd().parent / "tests" / "test_data" / "test_project" / "SGP 5.15.24 6.20.24 blanks"
)
site = "SGP"
start_time = "2024-05-15 00:00:00"
end_time = "2024-05-15 00:00:00"
filter_color = "white"
notes = "PUT THE NOTES HERE"
user = "JEMOEDER"
# TODO what to do with number of samples for the blanks
num_samples = 6  # In the file
vol_air_filt = 1  # L
wells_per_sample = 32
proportion_filter_used = 1.0  # between 0 and 1.0
vol_susp = 10  # mL
treatment = (
    # "base",
    # "heat",
    # "peroxide",
    "blank",
    # "blank heat",
    # "blank peroxide,"
)  # uncomment the one you want to use

# Use for side A
# dict_samples_to_dilution = {
#     "Sample_0": 1,
#     "Sample_1": 11,
#     "Sample_2": 121,
#     "Sample_3": 1331,
#     "Sample_4": 14641,
#     "Sample_5": float("inf"),
# }

# Use for side B
# dict_samples_to_dilution = {
#     "Sample_5": 1,
#     "Sample_4": 11,
#     "Sample_3": 121,
#     "Sample_2": 1331,
#     "Sample_1": 14641,
#     "Sample_0": float("inf"),
# }

# Use for Blanks
# dict_samples_to_dilution = {
#     "Sample_0" : float("inf"),
#     "Sample_1": 11,
#     "Sample_2": 1,
# }

dict_samples_to_dilution = {
    "Sample_0": float("inf"),
    "Sample_3": 11,
    "Sample_4": 1,
}

header = (
    f"site = {site}\nstart_time = {start_time}\nend_time = {end_time}\n"
    f"filter_color = {filter_color}\n"
    f"vol_air_filt = {vol_air_filt}\nproportion_filter_used = {proportion_filter_used}\n"
    f"vol_susp = {vol_susp}\ntreatment = {treatment[0]}\nnotes = {notes}\n"
    f"user = {user}\n"
)


if __name__ == "__main__":
    # checks for blank
    if not all(str(t) in str(test_folder) for t in treatment):
        print(
            f"your selection for treatment: {treatment} does not match with the specified "
            f"folder: {test_folder.name}"
        )
    if num_samples * wells_per_sample != 192:
        print(
            f"Number of samples * wells per sample ({num_samples}*{wells_per_sample} is "
            f"not equal to 192"
        )
    if "blank" in treatment:
        vol_air_filt = 1  # Always the case for blank

    # TODO: add check to see if num_samples is same as keys in dict

    # GUI
    window = tk.Tk()
    app = FreezingReviewer(window, test_folder, num_samples, includes=treatment)
    window.mainloop()

    # # Processing to create .csv file
    spaced_temp_csv = SpacedTempCSV(test_folder, num_samples, includes=treatment)
    # TODO: how to to deal with least diluted for when it's blanks with two experiments
    spaced_temp_csv.create_temp_csv(dict_samples_to_dilution)

    # Processing to create INPs/L
    # Use regular expression to check for dates in folder name:
    found_dates = re.findall(DATE_PATTERN, test_folder.name)
    for date in found_dates:
        month, day, year = date.split(".")
        start_year, str_start_month, start_day = start_time.split(" ")[0].split("-")
        start_month = int(str_start_month)
        if start_month < 10:
            start_month = int(str_start_month[1:])
            month = int(month[1:])
        if year != start_year[2:] or str(month) != str(start_month) or day != start_day:
            print(f"Date {date} does not match with the specified start time: {start_time}")
            ValueError("Date does not match with the specified start time")
            continue
        # add date to includes
        print(f"Processing data for: {site} {date}")
        includes = (date,) + treatment
        graph_data_csv = GraphDataCSV(
            test_folder,
            num_samples,
            vol_air_filt,
            wells_per_sample,
            proportion_filter_used,
            vol_susp,
            dict_samples_to_dilution,
            includes=includes,
        )
        graph_data_csv.convert_INPs_L(header)
