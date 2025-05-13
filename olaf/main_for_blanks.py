from pathlib import Path

from olaf.processing.blank_correction import BlankCorrector

# make decision on how many blanks to use
# iterate through project folder to find all the blank INPS/L
# take avg of all
project_folder = Path.cwd().parent / "tests" / "test_data" / "capek"
# iterate the project folder to find all the folders with "blanks" and therein all the
# "frozen_at_temp_reviewed" csv for "blanks"

# Make sure to have an indivdual "INPS_L_forzen_at_temp..." for each date
corrector = BlankCorrector(project_folder)
avg_blanks = corrector.average_blanks()
corrector.apply_blanks()
