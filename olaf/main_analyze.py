from olaf.processing.analyze import Analyze
from pathlib import Path

project_folder =  Path.cwd().parent / "tests" / "test_data" / "plotting_tests"

treatment_plot = Analyze(project_folder, treatment_plot = True)

#comparison_plot = Analyze(project_folder, comparison_plot = True)