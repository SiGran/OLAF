# OLAF - OpenSource Library for Automating Freezing

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-gh--pages-blue)](https://sigran.github.io/OLAF/)

**OLAF** is a Python toolkit for processing and analyzing data from Ice Nucleation Spectrometers (INS). It automates the workflow from raw freezing data to publication-ready Ice Nucleating Particle (INP) concentrations, complete with statistical analysis and quality control.

---

## Overview

OLAF streamlines the analysis of droplet freezing experiments used to quantify atmospheric Ice Nucleating Particles. The software provides:

- Automated processing of raw data from droplet freezing assays with multiple dilution series
- Interactive graphical user interface for manual validation of frozen well counts
- Calculation of INP concentrations per liter of air with confidence intervals using Agresti-Coull statistics
- Application of blank corrections to remove background contamination signals
- Generation of publication-ready outputs in ARM (Atmospheric Radiation Measurement) format
- Creation of visualizations for INP spectra quality control and analysis

### Key Features

**Automated Data Processing**: Converts raw temperature and frozen well data to INP concentrations
**GUI Validation Interface**: Review and correct frozen well counts with intuitive image-by-image navigation
**Statistical Rigor**: Agresti-Coull confidence intervals for binomial proportions
**Blank Correction**: Automated background subtraction with error propagation
**Multi-Treatment Support**: Combine base, heat, and peroxide treatments in final outputs
**ARM Format Compliance**: Generate files compatible with ARM data standards
**Quality Control**: Automated checks for monotonicity and threshold validation
**Comprehensive Testing**: 67+ unit and integration tests ensuring reliability and reproducibility

---

## Quick Start

### Installation

OLAF uses [`uv`](https://docs.astral.sh/uv/) for dependency management. For detailed installation instructions including platform-specific guidance, see the **[Installation Wiki](https://github.com/SiGran/OLAF/wiki)**.

```bash
# Clone the repository
git clone https://github.com/SiGran/OLAF.git
cd OLAF

# Create virtual environment and install dependencies
uv venv
uv sync

# Activate the environment
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

### Basic Usage

OLAF provides three main processing scripts corresponding to the analysis pipeline stages:

```bash
# Stage 1: Process individual experiments with GUI validation
python olaf/main.py

# Stage 2: Apply blank corrections to processed data
python olaf/main_for_blanks.py

# Stage 3: Combine treatments into ARM format files
python olaf/main_final_combine.py
```

See the **[User Guide](https://sigran.github.io/OLAF/)** for detailed workflow documentation.

---

## Processing Pipeline

OLAF implements a three-stage processing pipeline for INP data analysis:

```
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Raw Data Processing                                   │
│  - Load .dat files containing frozen well counts                │
│  - GUI validation of microscope images                          │
│  - Calculate INP concentrations with confidence intervals       │
│  Output: INPs_L_*.csv                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Blank Correction                                      │
│  - Average blank experiment measurements                        │
│  - Apply background subtraction with error propagation          │
│  - Enforce monotonicity and threshold checks                    │
│  Output: blank_corrected_*.csv                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Final Data Product Generation                         │
│  - Combine multiple treatments (base, heat, peroxide)           │
│  - Generate ARM-compliant output with metadata                  │
│  Output: final_files/*.csv                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Documentation

- **[Full Documentation](https://sigran.github.io/OLAF/)**: Comprehensive API reference, tutorials, and scientific methodology
- **[Installation Guide](https://github.com/SiGran/OLAF/wiki)**: Step-by-step installation for Windows, macOS, and Linux
- **[User Guide](https://sigran.github.io/OLAF/)**: Detailed workflow and usage instructions

---

## Project Structure

```
OLAF/
├── olaf/                      # Main package
│   ├── main.py               # Stage 1: Process raw data with GUI
│   ├── main_for_blanks.py    # Stage 2: Apply blank corrections
│   ├── main_final_combine.py # Stage 3: Generate ARM files
│   ├── CONSTANTS.py          # Scientific constants and thresholds
│   ├── processing/           # Core data processing modules
│   │   ├── graph_data_csv.py        # INP concentration calculations
│   │   ├── spaced_temp_csv.py       # Temperature binning
│   │   ├── blank_correction.py      # Background subtraction
│   │   └── final_file_creation.py   # ARM format generation
│   ├── image_verification/   # GUI for frozen well validation
│   │   ├── freezing_reviewer.py     # Main GUI application
│   │   ├── button_handler.py        # User interaction handling
│   │   └── data_loader.py           # Image and data loading
│   └── utils/                # Helper functions and utilities
├── tests/                    # Comprehensive test suite (67+ tests)
│   ├── test_integration/    # End-to-end pipeline tests
│   ├── test_processing/     # Core algorithm tests
│   └── test_utils/          # Utility function tests
├── docs/                     # Sphinx documentation source
└── data/                     # User data directory (experiments)
```

---

## Data Requirements

OLAF expects the following file structure for each experiment:

```
data/
└── your_experiment_MM.DD.YYYY/
    ├── *.dat                 # Tab-delimited freezing data
    └── *Images/              # Microscope images of 96-well plates
        └── *.png
```

The `.dat` file must contain the following columns: `Time`, `Avg_Temp`, `Sample_0` through `Sample_N`, and `Picture` (image filename references).

---

## Configuration

Configure each experiment by editing variables in `main.py`:

```python
# Experiment metadata
site = "SGP"                           # Site code (e.g., ARM site designation)
start_time = "2024-02-21 10:00:00"    # UTC start time
end_time = "2024-02-21 22:08:00"      # UTC end time
treatment = ("base",)                 # Treatment type

# Experimental parameters
num_samples = 6                       # Number of samples
vol_air_filt = 620.48                # Volume of air filtered (L)
wells_per_sample = 32                # Wells per sample in 96-well plate
vol_susp = 10                        # Suspension volume (mL)
proportion_filter_used = 1.0         # Fraction of filter used (0-1)

# Dilution series configuration
dict_samples_to_dilution = {
    "Sample_0": 1,
    "Sample_1": 11,
    "Sample_2": 121,
    "Sample_3": 1331,
    "Sample_4": 14641,
    "Sample_5": float("inf"),        # Undiluted suspension
}
```

---

## Output Files

### Stage 1 Outputs
- `reviewed_*.dat`: Corrected frozen well counts after GUI validation
- `frozen_at_temp_*.csv`: Frozen wells binned at 0.5°C temperature intervals
- `INPs_L_*.csv`: Ice Nucleating Particles per liter with confidence intervals
- `plot_*_INPs_L.png`: Optional INP spectrum visualization (toggled via `show_plot` parameter)

### Stage 2 Outputs
- `combined_blank_*.csv`: Averaged blank measurements across experiments
- `blank_corrected_*.csv`: INP data after blank subtraction and error propagation
- `blank_corrected_comp_plot_*.png`: Optional comparison plot (pre/post correction)

### Stage 3 Outputs
- `final_files/*.csv`: ARM-formatted files combining all treatments with unified metadata

---

## Scientific Methodology

OLAF implements established methods for INP quantification:

**Statistical Analysis**: Agresti-Coull confidence intervals for binomial proportions, providing more accurate coverage for extreme probability values common in INP measurements.

**Background Correction**: Root mean square error propagation for blank subtraction, with extrapolation for missing temperature ranges using linear regression on the last four data points.

**Quality Control**: Automated enforcement of physical constraints including monotonicity checks (INP concentration must increase or remain constant with decreasing temperature) and error threshold validation.

---

## Contributing

Contributions are welcome as this project is being prepared for v1.0 release. To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/descriptive-name`)
3. Commit your changes with clear, descriptive messages
4. Push to the branch (`git push origin feature/descriptive-name`)
5. Open a Pull Request

Please ensure all contributions meet the following standards:
- All tests pass (`pytest tests/`)
- Code follows project style guidelines (`ruff check`)
- New features include corresponding unit tests
- Documentation is updated to reflect changes

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See the [LICENSE](LICENSE) file for complete terms and conditions.

---

## Citation

If you use OLAF in your research, please cite:

```
OLAF: OpenSource Library for Automating Freezing
Grannetia, S. et al. (2025)
OLAF v1.0: Automated processing of Ice Nucleation Spectrometer data
DOI: [Pending publication]
```

---

## Contact and Support

**Developer**: Simon Grannetia
**Organization**: [TrackDat on LinkedIn](https://www.linkedin.com/company/trackdat)
**Repository**: [https://github.com/SiGran/OLAF](https://github.com/SiGran/OLAF)
**Issues and Bug Reports**: [https://github.com/SiGran/OLAF/issues](https://github.com/SiGran/OLAF/issues)

---

## Acknowledgments

This work has been supported by:
- Atmospheric Radiation Measurement (ARM) user facility, a U.S. Department of Energy (DOE) Office of Science user facility
- Colorado State University Department of Atmospheric Science
- The atmospheric science research community for valuable feedback and testing

Development of OLAF benefits from open-source scientific Python packages including NumPy, Pandas, Matplotlib, and the Pytest testing framework.

---

<div align="center">

**[Documentation](https://sigran.github.io/OLAF/)** • **[Installation Guide](https://github.com/SiGran/OLAF/wiki)** • **[Report Issues](https://github.com/SiGran/OLAF/issues)**

</div>
