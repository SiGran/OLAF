import re
import tkinter as tk
from datetime import datetime
from pathlib import Path

from olaf.CONSTANTS import DATE_PATTERN
from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.processing.spaced_temp_csv import SpacedTempCSV

# -----------------------------    USER INPUTS    -------------------------------------
#test_folder = Path.cwd().parent / "tests" /"test_data" / "fpd" / "NSA no.2 05.22.25 base"
test_folder = Path("D:/OLAF/Freezing point depression tests/capek mock test 12.31.24 base")
#test_folder = Path("G:/Shared drives/INP Mentor/Current Data Processing/CAPE_k/QAQC as of 03.04.26_CH/2024/KCG 09.23.24 peroxide bl")
site = "na"
start_time = "2024-12-31 04:05:00"
end_time = "2024-12-31 04:05:00"
filter_color = "white"
notes = "testing"
user = "Carson"
IS = "na"
num_samples = 6  # In the file
sample_type = "salt"  # air, liquid or soil
vol_air_filt = 1.0 # L
wells_per_sample = 32
proportion_filter_used = 1.0  # between 0 and 1.0
vol_susp = 10  # mL
treatment = (
     "base",
    # "heat",
    # "peroxide",
    # "blank",
    # "blank heat",
    # "blank peroxide,"
)  # uncomment the one you want to use

# Use for side A or IS2
dict_samples_to_dilution = {
    "Sample_0": 1,
    "Sample_1": 11,
    "Sample_2": 121,
    "Sample_3": 1331,
    "Sample_4": 14641,
    "Sample_5": float("inf"),
}

# Use for side B
# dict_samples_to_dilution = {
#     "Sample_5": 1.5,
#     "Sample_4": 16.5,
#     "Sample_3": 181.5,
#     "Sample_2": 1996.5,
#     #"Sample_1": 14641,
#     "Sample_0": float("inf"),
# }

# ----------------------------    EXTRA INFO IF NEEDED  ---------------------------------
# if running filters from TBS
lower_altitude = 0  # m agl
upper_altitude = 0  # m agl

# if sample is soil
dry_mass = 2  # dried mass of soil in g

# if seawater or other salty sample, use this to estimate freezing point depression
# use this formula: {dilution:adjustment}
freezing_point_depression_dict = {1:2, 11:0.2}


# ----------------------- Assembling the header for the CSV file -----------------------
header = (
    f"site = {site}\nstart_time = {start_time}\nend_time = {end_time}\n"
    f"filter_color = {filter_color}\nsample_type = {sample_type}\n"
    f"vol_air_filt = {vol_air_filt}\nproportion_filter_used = {proportion_filter_used}\n"
    f"vol_susp = {vol_susp}\ntreatment = {treatment[0]}\nnotes = {notes}\n"
    f"user = {user}\nIS = {IS}\n"
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

    # Few automatic variable assignments and optional header additions
    if "blank" in treatment or sample_type != "air":
        vol_air_filt = 1  # Always the case for blank

    if "soil" in sample_type:
        vol_air_filt = vol_susp / dry_mass

    if "TBS" in site:
        header += f"lower_altitude = {lower_altitude}\nupper_altitude = {upper_altitude}\n"


    # GUI
    window = tk.Tk()
    app = FreezingReviewer(
        window,
        test_folder,
        num_samples,
        wells_per_sample,
        dict_samples_to_dilution,
        includes=treatment,
    )
    window.mainloop()

    # # Processing to create .csv file
    spaced_temp_csv = SpacedTempCSV(test_folder, num_samples, includes=treatment)
    spaced_temp_csv.create_temp_csv(dict_samples_to_dilution)

    # Processing to create INPs/L
    # Use regular expression to check for dates in folder name:
    found_dates = re.findall(DATE_PATTERN, test_folder.name)
    if not found_dates:
        print("No date found in folder name")
    for date in found_dates:
        # Convert `date` to datetime object
        date_obj = datetime.strptime(date, "%m.%d.%y")

        # Convert `start_time` to datetime object
        start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

        # Compare the two dates
        if date_obj.date() != start_time_obj.date():
            print(f"Date {date} does not match with the specified start time: {start_time}")
            ValueError("Date does not match with the specified start time")
            continue
        # add date to includes
        print(f"Processing data for: {site} {date}")
        includes = (date,) + treatment
        # TODO: make the changes work for sample_type see issue #18 on github
        graph_data_csv = GraphDataCSV(
            test_folder,
            num_samples,
            sample_type,
            vol_air_filt,
            wells_per_sample,
            proportion_filter_used,
            vol_susp,
            dict_samples_to_dilution,
            freezing_point_depression_dict,
            includes=includes,
        )
        graph_data_csv.convert_INPs_L(header, show_plot=True)
