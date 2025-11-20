from olaf.processing.plots import Plots
from pathlib import Path

project_folder =  Path.cwd().parent / "tests" / "test_data" / "plotting_tests"
includes = ("INPs_L", "frozen_at_temp", "reviewed")
excludes = ("blanks",)
date_range =

plot = Plots(project_folder, includes, excludes)
