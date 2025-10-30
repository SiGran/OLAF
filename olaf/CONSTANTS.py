"""Constants used throughout the OLAF package for INP data processing."""

# ============================================================================
# Well and Volume Constants
# ============================================================================
VOL_WELL = 50  # microL - volume per well in 96-well plate

# ============================================================================
# Statistical Constants
# ============================================================================
Z = 1.96  # Z-score for 95% confidence interval

# How many wells less than total number of wells should be excluded from calculations.
# See Agresti-Coull 1998.
AGRESTI_COULL_UNCERTAIN_VALUES = 2

# Number of temperature samples that the highest dilution needs to have more frozen wells
# to replace the background
NUM_TO_REPLACE_D1 = 10

# ============================================================================
# Temperature Constants
# ============================================================================
TEMP_ROUNDING_INTERVAL = 0.5  # Celsius - temperature binning interval
TEMP_TOLERANCE = 0.01  # Celsius - tolerance for temperature comparisons
INITIAL_ROWS_FOR_TEMP = 4  # Number of initial rows for temperature data

# ============================================================================
# Unit Conversion Constants
# ============================================================================
MICROLITERS_TO_ML = 0.001  # Conversion factor from microliters to milliliters

# ============================================================================
# Plot Configuration Constants
# ============================================================================
# Skip first N data points when plotting (for data quality)
PLOT_SKIP_FIRST_N_POINTS = 4

# Temperature axis configuration
TEMP_AXIS_MIN = -30  # Celsius - minimum temperature on plot
TEMP_AXIS_MAX = 0    # Celsius - maximum temperature on plot
TEMP_MAJOR_TICK_INTERVAL = 5  # Celsius - major tick interval
TEMP_MINOR_TICK_INTERVAL = 1  # Celsius - minor tick interval

# Axis limit multipliers for automatic scaling
AXIS_LOWER_LIMIT_FACTOR = 0.1  # Multiply minimum value for lower bound
AXIS_UPPER_LIMIT_FACTOR = 3.0  # Multiply maximum value for upper bound

# ============================================================================
# Error Handling Constants
# ============================================================================
ERROR_SIGNAL = -9999  # Signal value when data is set to be an error
# Percentage - threshold for blank corrected INPS_L
# to be allowed below uncorrected CI
THRESHOLD_ERROR = 10
NEAR_ZERO_THRESHOLD = 1e-10  # Threshold for checking if a value is near zero

# ============================================================================
# File and Date Pattern Constants
# ============================================================================
# Regex pattern for date in filenames (MM.DD.YY format)
DATE_PATTERN = r"(?<!\d)(\d{1,2}\.\d{1,2}\.\d{2})(?!\d)"
