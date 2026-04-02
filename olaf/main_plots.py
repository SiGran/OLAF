from pathlib import Path

from olaf.processing.plots import Plots

#project_folder =  Path.cwd().parent / "data" / "PUFIN tests"
#project_folder = Path("D:/INP Mentor/Long term sites/NSA/data/12.01.25 test")
project_folder = Path("G:/Shared drives/INP Mentor/Current Data Processing/CAPE_k/QAQC as of 03.04.26_CH/2024")
#project_folder = Path("D:/INP Mentor/Long term sites/BNF/TBS/Data/May-June 2025")
## NOTE ^ this method works but plots everything in a strange order

includes = ("INPs_L", "frozen_at_temp", "reviewed")
excludes = ()
start_date = "07.24.24" #earliest date you want as part of the analysis
end_date = "07.24.24" # latest date

# if making subplots, designate number of desired columns here
num_columns = 3

# how you want the image saved
save_name = "BNF spring 2025 TBS overview"

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
