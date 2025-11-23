from datetime import datetime

from olaf.processing.plots import Plots
from pathlib import Path

project_folder =  Path.cwd().parent / "tests" / "test_data" / "plotting_tests"
includes = ("INPs_L", "frozen_at_temp", "reviewed")
excludes = ("blanks",)
start_date = "08.22.24"
end_date = "04.30.25"

# if making subplots, designate number of desired columns here
num_columns = 3

# TODO: Add option for site comparison plotting for co-located projects

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
    num_columns)
plot.plot_data(subplots=True)
