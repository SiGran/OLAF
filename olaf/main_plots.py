from pathlib import Path

from olaf.processing.plots import Plots

#project_folder =  Path.cwd().parent / "data" / "PUFIN tests"

project_folder = Path("D:/INP Mentor/IOPs/TRACER/Swarup China S3 Heat treatments")
#project_folder = test_folder = Path("G:/Shared drives/INP Mentor/Archived Data/CoURAGE/Ground/QAQC as of 04.28.26 CH")


includes = ("INPs_L", "frozen_at_temp", "reviewed")
excludes = ()
start_date = "05.08.22" #earliest date you want as part of the analysis
end_date = "10.08.22" # latest date

# if making subplots, designate number of desired columns here
num_columns = 2

# how you want the image saved
save_name = "Swarup overview 2"

# if you are doing a site comparison, type them here and decide on marker style
#site_markers = {"CRG_M1": "o", "CRG_S2": "^", "CRG_S7_TBS": "o", "KCG_S3": "o"}
# or default markers if you leave the dict empty
site_markers = {}


# Creates images of INP spectra for each date in project folder.
# Plots treatments for same date on one plot.
# Subplots = True creates on image with all INP spectra
# Subplots = False creates individual images for each date
# Site comparison = True iterates through all samples with same date and plots
# both sites on a single plot and timestamps are removed from plot title when true.
# TBS = True sets the "site" parameter to altitude range and plots each altitude
# range per day on the same plot
plot = Plots(
    project_folder,
    includes,
    excludes,
    start_date,
    end_date,
    num_columns,
    site_markers,
    save_name=save_name)
plot.plot_data(subplots=True, site_comparison=False, tbs = False)

# temps = [-10.0, -15.0, -20.0, -25.0]
# treatments = ["base"]
# plot.desired_temp_csv(temps, treatments)
