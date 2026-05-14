# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Operating Rules

**File deletions are not allowed.** The agent must never delete files or directories,
never run `rm`, `rmdir`, `git rm`, `Path.unlink`, `shutil.rmtree`, or any equivalent
operation, and never call tools that delete. This applies even when "replacing" a file:
if an existing file must be superseded, the agent creates the replacement alongside
(e.g. `foo.py.new`) and adds a checkbox under "Human-Needs-To-Do" in `TODO.md` for the
human to perform the deletion / rename manually. The agent may *overwrite* file contents
through the editing tools (that is not deletion), but must not remove paths from disk.

## Project Overview

OLAF (OpenSource Library for Automating Freezing) is a Python toolkit for processing Ice Nucleation Spectrometer (INS) data. It automates the workflow from raw droplet freezing data to publication-ready Ice Nucleating Particle (INP) concentrations with statistical analysis and quality control.

**Key Scientific Concepts:**
- Processes droplet freezing experiments to quantify atmospheric Ice Nucleating Particles
- Uses Agresti-Coull statistics for binomial confidence intervals
- Implements blank correction with error propagation
- Generates ARM (Atmospheric Radiation Measurement) format outputs

## Common Development Commands

### Environment Setup
```bash
# Install dependencies (uses uv package manager)
uv sync

# Install with dev dependencies
uv sync --all-extras
```

### Testing
```bash
# Run all tests from project root
pytest tests/

# Run with coverage report
pytest tests/ --cov=olaf --cov-report=term-missing

# Run specific test file
pytest tests/test_processing/test_graph_data_csv.py

# Run specific test function
pytest tests/test_processing/test_graph_data_csv.py::test_function_name

# Run integration tests only
pytest tests/test_integration/
```

### Code Quality
```bash
# Lint code with ruff (line length: 100)
ruff check olaf/

# Auto-fix linting issues
ruff check --fix olaf/

# Type checking with mypy
mypy olaf/

# Security analysis with bandit
bandit -r olaf/

# Run pre-commit hooks
pre-commit run --all-files
```

### Running the Application
```bash
# Stage 1: Process raw data with GUI validation (from olaf/ directory)
python main.py

# Stage 2: Apply blank corrections
python main_for_blanks.py

# Stage 3: Generate final ARM files
python main_final_combine.py
```

### Documentation
```bash
# Build Sphinx documentation (from docs/ directory)
cd docs
make html

# View built docs at docs/_build/html/index.html
```

## Architecture Overview

### Three-Stage Processing Pipeline

OLAF implements a sequential three-stage pipeline for INP data analysis:

**Stage 1 (`main.py`)**: Raw data processing with GUI validation
- Loads `.dat` files containing frozen well counts and temperature data
- Opens GUI (`FreezingReviewer`) for manual validation of microscope images
- Creates temperature-binned frozen well counts (`frozen_at_temp_*.csv`)
- Calculates INP concentrations with Agresti-Coull confidence intervals (`INPs_L_*.csv`)
- User configures experiment parameters directly in the script (site, dates, dilutions, etc.)

**Stage 2 (`main_for_blanks.py`)**: Background correction
- Finds all blank experiment files in project folder
- Averages blank measurements across multiple runs
- Applies blank subtraction with root mean square error propagation
- Enforces monotonicity checks and threshold validation
- Outputs `blank_corrected_*.csv` files

**Stage 3 (`main_final_combine.py`)**: Final data product generation
- Combines multiple treatments (base, heat, peroxide) from same date
- Generates ARM-compliant CSV files with standardized metadata
- Outputs to `final_files/` directory

### Key Processing Modules

**`processing/graph_data_csv.py` (`GraphDataCSV` class)**
- Core INP calculation engine
- Converts frozen wells to INPs/L using the formula: `INP/mL = -LN((Dx-Ex)/Dx)/(Cx/1000)*Fx`
- Implements Agresti-Coull confidence intervals (see CONSTANTS.py for Z-score)
- Handles dilution series with background replacement logic
- Outputs include optional plots when `show_plot=True`

**`processing/spaced_temp_csv.py` (`SpacedTempCSV` class)**
- Bins frozen well counts into 0.5°C temperature intervals (see `TEMP_ROUNDING_INTERVAL` in CONSTANTS.py)
- Creates intermediate `frozen_at_temp_*.csv` files for Stage 1

**`processing/blank_correction.py` (`BlankCorrector` class)**
- Manages complete blank correction workflow
- Finds latest blank files using date regex matching
- Averages blanks with linear extrapolation for missing temperature ranges
- Validates corrected data against `THRESHOLD_ERROR` percentage

**`processing/final_file_creation.py` (`FinalFileCreation` class)**
- Combines treatments using configurable `treatment_dict` (maps treatment names to integer flags)
- Applies ARM format headers and metadata

### GUI System

**`image_verification/freezing_reviewer.py` (`FreezingReviewer` class)**
- Tkinter-based interactive GUI for manual validation
- Inheritance: `FreezingReviewer` → `ButtonHandler` → `DataLoader`
- Displays microscope images of 96-well plates
- Allows per-sample well count adjustments (+1/-1 buttons)
- Enforces monotonicity: frozen wells must increase or stay constant with decreasing temperature
- Saves corrected data as `reviewed_*.dat` files

**`image_verification/button_handler.py` (`ButtonHandler` class)**
- Manages GUI event handling and user interactions
- Controls image navigation (back/forward)

**`image_verification/data_loader.py` (`DataLoader` class)**
- Loads `.dat` files and microscope images
- Base class for data management

### Utility Modules

**`utils/data_handler.py` (`DataHandler` class)**
- Base class for file finding and CSV reading
- Uses `includes` and `excludes` tuples for flexible file filtering
- Provides consistent data loading interface

**`utils/df_utils.py`**
- `header_to_dict()`: Parses multi-line CSV headers into dictionaries
- `read_with_flexible_header()`: Handles CSV files with variable header lengths
- `unique_dilutions()`: Extracts unique dilution factors from data

**`utils/math_utils.py`**
- `inps_L_to_ml()` and `inps_ml_to_L()`: Unit conversions
- `rms()`: Root mean square for error propagation

**`utils/path_utils.py`**
- `find_latest_file()`: Finds most recent file matching pattern
- `sort_files_by_date()`: Groups files by date using regex
- `is_within_dates()`: Validates date ranges for blank correction

**`utils/plot_utils.py`**
- `plot_INPS_L()`: Creates INP spectrum visualizations
- `plot_blank_corrected_vs_pre_corrected_inps()`: Comparison plots for blank correction

**`CONSTANTS.py`**
- Centralized scientific constants and thresholds
- Critical values: `VOL_WELL` (50 µL), `Z` (1.96 for 95% CI), `TEMP_ROUNDING_INTERVAL` (0.5°C)
- Error handling: `ERROR_SIGNAL` (-9999), `THRESHOLD_ERROR` (10%)
- When modifying processing logic, check if relevant constants exist here first

## Configuration and Usage Patterns

### Experiment Configuration
Each processing stage is configured by editing variables directly in the main scripts:

```python
# In main.py
site = "SGP"                           # Site code
start_time = "2024-02-21 10:00:00"    # UTC timestamps
end_time = "2024-02-21 22:08:00"
treatment = ("base",)                  # Can be "base", "heat", "peroxide", "blank"
num_samples = 6
vol_air_filt = 620.48                 # Liters of air filtered
wells_per_sample = 32                 # Must satisfy: num_samples * wells_per_sample = 192
vol_susp = 10                         # mL
proportion_filter_used = 1.0          # Fraction (0-1)

dict_samples_to_dilution = {
    "Sample_0": 1,
    "Sample_1": 11,
    "Sample_2": 121,
    "Sample_3": 1331,
    "Sample_4": 14641,
    "Sample_5": float("inf"),        # Undiluted suspension (background)
}
```

### Data File Structure
OLAF expects specific file organization:

```
data/your_experiment_MM.DD.YYYY/
├── *.dat                 # Tab-delimited with columns: Time, Avg_Temp, Sample_0..Sample_N, Picture
└── *Images/              # Microscope images referenced in Picture column
    └── *.png
```

### File Naming Conventions
- Date pattern in filenames: `MM.DD.YY` format (e.g., "02.21.24")
- Stage 1 outputs: `INPs_L_frozen_at_temp_*.csv`, `reviewed_*.dat`
- Stage 2 outputs: `blank_corrected_*.csv`, `combined_blank_*.csv`
- Stage 3 outputs: Stored in `final_files/` subdirectory

### Testing Data
Test data fixtures are defined in `tests/conftest.py`:
- `test_data_root`: Locates test data directory
- `sgp_test_folder`: Standard SGP test dataset
- `sample_dilution_dict`: Standard dilution series for tests
- Integration tests in `tests/test_integration/test_full_pipeline.py` validate end-to-end workflow

## Important Development Notes

### Working with Main Scripts
The three main scripts (`main.py`, `main_for_blanks.py`, `main_final_combine.py`) are designed as user-configurable scripts rather than libraries. Users edit variables at the top of each file to configure experiments. When making changes:
- Preserve the user configuration section at the top
- Maintain clear separation between config and processing logic
- Keep validation checks (e.g., treatment matching folder name)

### Error Handling
- Missing values and below-detection-limit data use `ERROR_SIGNAL = -9999`
- Blank correction validates that corrected INPs don't drop below uncorrected confidence intervals by more than `THRESHOLD_ERROR` (10%)
- Zero/negative INPs are filtered during blank averaging

### Statistical Methods
- Agresti-Coull confidence intervals are preferred over Wald for binomial proportions
- `AGRESTI_COULL_UNCERTAIN_VALUES = 2` excludes edge cases per Agresti-Coull 1998
- Blank correction uses RMS error propagation for confidence interval adjustment

### GUI Behavior
- Clicking "-1" on a sample propagates backwards to when that well first froze (enforces monotonicity)
- Clicking "+1" on a sample applies change forward from current image
- Wells are clamped between 0 and `wells_per_sample`
- Changes are stored in a "changes" column for audit trail

### Code Style
- Line length: 100 characters (enforced by ruff)
- Python 3.11+ required (uses modern type hints like `|` for Union)
- Type stubs available for pandas via `pandas-stubs`

### Working Directory
All main scripts expect to be run from the `olaf/` subdirectory with project data in `../data/` or `../tests/test_data/`.