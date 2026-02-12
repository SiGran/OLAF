from pathlib import Path

from olaf.processing.blank_correction import BlankCorrector

# make decision on how many blanks to use
# iterate through project folder to find all the blank INPS/L
# take average of all blanks
project_folder = Path.cwd().parent / "tests" / "test_data" / "NSA_qc_flag_test"
blank_includes = ("INPs_L_frozen_at_temp_reviewed", "blank")
blank_excludes = ()

# Any samples you don't want blank corrected go in sample_excludes
sample_excludes = ("05.22.25",)
# Make sure to have an individual "INPS_L_frozen_at_temp..." for each date
corrector = BlankCorrector(
    project_folder,
    blank_includes,
    blank_excludes,
    sample_excludes,
    multiple_per_day=True)
avg_blanks = corrector.average_blanks()
corrector.apply_blanks(only_within_dates=False, show_comp_plot=True)
