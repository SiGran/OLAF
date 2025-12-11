from pathlib import Path

from olaf.processing.plots import Plots

project_folder =  Path.cwd().parent / "data" / "CRG" / "Ground"
includes = ("INPs_L", "frozen_at_temp", "reviewed", "base")
excludes = ("blank","heat","peroxide")
start_date = "03.23.24" #earliest date you want as part of the analysis
end_date = "07.25.25" # latest date

# if making subplots, designate number of desired columns here
num_columns = 4

# how you want the image saved
save_name = "CRG site comparison 12.01.24 thru 7.25.25 BASE ONLY"

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
