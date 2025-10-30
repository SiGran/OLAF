# OLAF - OpenSource Library for Automating Freezing

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-gh--pages-blue)](https://sigran.github.io/OLAF/)

**OLAF** is a Python toolkit for processing and analyzing data from Ice Nucleation Spectrometers (INS), also known as Ice Spectrometers (IS). It automates the workflow from raw freezing data to publication-ready Ice Nucleating Particle (INP) concentrations, complete with statistical analysis and quality control.

---

## 🔬 What is OLAF?

OLAF streamlines the analysis of droplet freezing experiments used to quantify atmospheric Ice Nucleating Particles. The software:

- **Processes raw data** from droplet freezing assays with multiple dilution series
- **Provides interactive GUI** for manual validation of frozen well counts
- **Calculates INP concentrations** per liter of air with confidence intervals using Agresti-Coull statistics
- **Applies blank corrections** to remove background contamination signals
- **Generates publication-ready outputs** in ARM (Atmospheric Radiation Measurement) format
- **Creates visualizations** of INP spectra for quality control and analysis

### Key Features

✅ **Automated Data Processing**: Converts raw temperature and frozen well data to INP concentrations
✅ **GUI Validation Interface**: Review and correct frozen well counts with intuitive image-by-image interface
✅ **Statistical Rigor**: Agresti-Coull confidence intervals for binomial proportions
✅ **Blank Correction**: Automated background subtraction with error propagation
✅ **Multi-Treatment Support**: Combine base, heat, and peroxide treatments in final outputs
✅ **ARM Format Compliance**: Generate files compatible with ARM data standards
✅ **Quality Control**: Automated checks for monotonicity and threshold validation
✅ **Comprehensive Testing**: 67+ tests ensuring reliability and reproducibility

---

## 🚀 Quick Start

### Installation

OLAF uses [`uv`](https://docs.astral.sh/uv/) for dependency management. For detailed installation instructions, see the **[Installation Wiki](https://github.com/SiGran/OLAF/wiki)**.

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

OLAF provides three main processing scripts:

```python
# 1. Process individual experiments (with GUI validation)
python olaf/main.py

# 2. Apply blank corrections to processed data
python olaf/main_for_blanks.py

# 3. Combine treatments into ARM format files
python olaf/main_final_combine.py
```

See the **[User Guide](https://sigran.github.io/OLAF/)** for detailed workflow documentation.

---

## 📊 Workflow

OLAF follows a three-stage processing pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Raw Data → INPs/L                                     │
│  - Load .dat files with frozen well counts                      │
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
│  Stage 3: Final ARM Format Files                                │
│  - Combine multiple treatments (base, heat, peroxide)           │
│  - Generate ARM-compliant output with metadata                  │
│  Output: final_files/*.csv                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

- **[Full Documentation](https://sigran.github.io/OLAF/)**: Comprehensive API reference, tutorials, and examples
- **[Installation Guide](https://github.com/SiGran/OLAF/wiki)**: Step-by-step installation for Windows, macOS, and Linux
- **[User Guide](https://sigran.github.io/OLAF/)**: Detailed workflow and usage instructions

---

## 📁 Project Structure

```
OLAF/
├── olaf/                      # Main package
│   ├── main.py               # Stage 1: Process raw data with GUI
│   ├── main_for_blanks.py    # Stage 2: Apply blank corrections
│   ├── main_final_combine.py # Stage 3: Generate ARM files
│   ├── CONSTANTS.py          # Scientific constants
│   ├── processing/           # Core data processing modules
│   ├── image_verification/   # GUI for frozen well validation
│   └── utils/                # Helper functions
├── tests/                    # Comprehensive test suite (67+ tests)
├── docs/                     # Sphinx documentation source
└── data/                     # User data directory (experiments)
```

---

## 🧪 Data Requirements

OLAF expects the following file structure for each experiment:

```
data/
└── your_experiment_MM.DD.YYYY/
    ├── *.dat                 # Tab-delimited freezing data
    └── *Images/              # Microscope images of 96-well plates
        └── *.png
```

The `.dat` file should contain columns: `Time`, `Avg_Temp`, `Sample_0` through `Sample_N`, and `Picture` filename references.

---

## 🔧 Configuration

Configure each experiment by editing variables in `main.py`:

```python
# Experiment metadata
site = "SGP"                           # Site code (e.g., ARM site)
start_time = "2024-02-21 10:00:00"    # UTC start time
end_time = "2024-02-21 22:08:00"      # UTC end time
treatment = ("base",)                 # Treatment type

# Experimental parameters
num_samples = 6                       # Number of samples
vol_air_filt = 620.48                # Volume of air filtered (L)
wells_per_sample = 32                # Wells per sample in 96-well plate
vol_susp = 10                        # Suspension volume (mL)
proportion_filter_used = 1.0         # Fraction of filter used

# Dilution series
dict_samples_to_dilution = {
    "Sample_0": 1,
    "Sample_1": 11,
    "Sample_2": 121,
    "Sample_3": 1331,
    "Sample_4": 14641,
    "Sample_5": float("inf"),        # Undiluted
}
```

---

## 📈 Output Files

### Stage 1 Outputs
- `reviewed_*.dat`: Corrected frozen well counts after GUI validation
- `frozen_at_temp_*.csv`: Frozen wells at 0.5°C temperature bins
- `INPs_L_*.csv`: Ice Nucleating Particles per liter with confidence intervals
- `plot_*_INPs_L.png`: Optional INP spectrum visualization

### Stage 2 Outputs
- `combined_blank_*.csv`: Averaged blank measurements
- `blank_corrected_*.csv`: INP data after blank subtraction
- `blank_corrected_comp_plot_*.png`: Optional pre/post correction comparison

### Stage 3 Outputs
- `final_files/*.csv`: ARM-formatted files combining all treatments

---

## 🤝 Contributing

Contributions are welcome! This project is being prepared for v1.0 release with comprehensive documentation and testing.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes with clear messages
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- ✅ All tests pass (`pytest tests/`)
- ✅ Code follows style guidelines (`ruff check`)
- ✅ New features include tests
- ✅ Documentation is updated

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

---

## 📖 Citation

If you use OLAF in your research, please cite:

> **OLAF: OpenSource Library for Automating Freezing**
> Grannetia, S. et al. (2025). OLAF v1.0: Automated processing of Ice Nucleation Spectrometer data.
> DOI: [Coming soon]

---

## 📧 Contact

**Author**: Simon Grannetia
**Email**: simongrannetia@gmail.com
**Repository**: [https://github.com/SiGran/OLAF](https://github.com/SiGran/OLAF)
**Issues**: [https://github.com/SiGran/OLAF/issues](https://github.com/SiGran/OLAF/issues)

---

## 🙏 Acknowledgments

- Atmospheric Radiation Measurement (ARM) program for data format standards
- Colorado State University for supporting this research
- The atmospheric science community for feedback and testing

---

<div align="center">

**[Documentation](https://sigran.github.io/OLAF/)** • **[Installation Guide](https://github.com/SiGran/OLAF/wiki)** • **[Report Issues](https://github.com/SiGran/OLAF/issues)**

Made with ❄️ for the Ice Nucleation research community

</div>
