from pathlib import Path

from olaf.CONSTANTS import ERROR_SIGNAL
from olaf.processing.final_file_creation import FinalFileCreation

project_folder = Path.cwd().parent / "data" / "BNF" / "TBS" / "test3"
includes = ("INPs_L", "frozen_at_temp", "reviewed", "blank_corrected", "10%")
excludes = ("blanks",)
treatment_dict = {"base": 0, "heat": 1, "peroxide": 2}
header_start = (
    f"ARM Mentor: Jessie Creamean at Colorado State University\n"
    f"Contact: Jessie.Creamean@colostate.edu; cchume@rams.colostate.edu\n"
    f"Data: Number of ice nucleating particles per L of air at STP (0 degC and 101.325 kPa); "
    f"lower 95 percent confidence limit; upper 95 percent confidence limit\n"
    f"For access to all filter metadata (e.g. flows times sites notes etc.) visit "
    f"https://docs.arm.gov/share/s/BkJRSN5mR1mcZKjZm13Vtw\n"
    f"Treatment flags: 0 = untreated; 1 = heat treated; and 2 = peroxide treated\n"
    f"Missing values or values below detection limit are denoted as {ERROR_SIGNAL}\n"
)

# look for all "blank_corrected_INPS_L" files
to_final_file = FinalFileCreation(project_folder, includes, excludes)
to_final_file.create_all_final_files(treatment_dict, header_start)
