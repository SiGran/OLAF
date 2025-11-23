from datetime import datetime

from olaf.processing.plots import Plots
from pathlib import Path

project_folder =  Path.cwd().parent / "tests" / "test_data" / "plotting_tests"
includes = ("INPs_L", "frozen_at_temp", "reviewed")
excludes = ("blanks",)
start_date = "08.22.24"
end_date = "04.30.25"



plot = Plots(project_folder, includes, excludes, start_date, end_date)
plot.plot_data(subplots=True)
