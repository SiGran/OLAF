from pathlib import Path

from olaf.processing.plots import Plots

project_folder =  Path.cwd().parent / "tests" / "test_data" / "plotting_tests"
includes = ("INPs_L", "frozen_at_temp", "reviewed")
excludes = ("blanks",)
start_date = "08.22.24" #earliest date you want as part of the analysis
end_date = "04.30.25" # latest date

# if making subplots, designate number of desired columns here
num_columns = 2

# how you want the image saved
save_name = "1Courage site comparison Dec 2024 thru Apr 2025"

# if you are doing a site comparison, type them here and decide on marker style
site_markers = {"CRG_M1": "o", "CRG_S2": "^"}

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
plot.plot_data(subplots=True, site_comparison=True)
