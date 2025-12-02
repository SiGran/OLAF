from pathlib import Path

from olaf.processing.plots import Plots

project_folder =  Path.cwd().parent / "data" / "CRG" / "TBS" / "July 2025 blanks by day"
includes = ("INPs_L", "frozen_at_temp", "reviewed", "blank_corrected", "10%")
excludes = ("none",)
start_date = "07.22.25" #earliest date you want as part of the analysis
end_date = "07.23.25" # latest date

# if making subplots, designate number of desired columns here
num_columns = 2

# how you want the image saved
save_name = "CRG TBS 07.22.25"

# if you are doing a site comparison, type them here and decide on marker style
site_markers = {"CRG_M1": "o", "CRG_S2": "^", "CRG_S7_TBS": "o"}

# Creates images of INP spectra for each date in project folder.
# Plots treatments for same date on one plot.
# Subplots = True creates on image with all INP spectra
# Subplots = False creates individual images for each date
plot = Plots(
    project_folder,
    includes,
    excludes,
    start_date,
    end_date,
    num_columns,
    site_markers,
    save_name)
plot.plot_data(subplots=True, site_comparison=True, tbs = True)
