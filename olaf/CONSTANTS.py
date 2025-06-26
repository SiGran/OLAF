VOL_WELL = 50  # microL

# Number of temperature samples that the highest dilution needs to have more frozen wells
# to replace the background
NUM_TO_REPLACE_D1 = 10
Z = 1.96  # 95% confidence interval

# Threshold for blank corrected INPS_L to be allowed to be below uncorrected CI
THRESHOLD_ERROR = 10  # Percentage!!!
ERROR_SIGNAL = -9999  # Signal when values are set to be an error

# date pattern for file name
DATE_PATTERN = r"(?<!\d)(\d{1,2}\.\d{1,2}\.\d{2})(?!\d)"

# How many wells less than total number of wells should be excluded from calculations.
# See Agresti-Coull 1998.
AGRESTI_COULL_UNCERTAIN_VALUES = 2
