Usage Guide
===========

OLAF implements a three-stage sequential pipeline for processing Ice Nucleation
Spectrometer (INS) data. Each stage is run as a module from the repository root and is
driven by a ``.toml`` configuration file (see ``configs/templates/`` and
``configs/README.md``).

Stage 1: Raw Data Processing (``main.py``)
-------------------------------------------

This stage processes raw ``.dat`` files from the INS instrument, opens a GUI for
manual validation of microscope images, and computes INP concentrations.

**Configuration:**

Copy ``configs/templates/main.example.toml`` into your campaign folder
(``configs/<CAMPAIGN>/process/``) and edit the values:

.. code-block:: toml

   data_folder = "data/SGP 2.21.24 base"
   site = "SGP"
   start_time = "2024-02-21 10:00:00"   # UTC
   end_time = "2024-02-21 22:08:00"
   treatment = ["base"]                  # "base", "heat", "peroxide", or "blank"
   num_samples = 6
   vol_air_filt = 620.48                 # Liters of air filtered
   wells_per_sample = 32                 # Must satisfy: num_samples * wells_per_sample = 192
   vol_susp = 10                         # mL
   proportion_filter_used = 1.0

   [dict_samples_to_dilution]
   Sample_0 = 1
   Sample_1 = 11
   Sample_2 = 121
   Sample_3 = 1331
   Sample_4 = 14641
   Sample_5 = inf                        # Background (undiluted)

**Running:**

.. code-block:: bash

   python -m olaf.main configs/<CAMPAIGN>/process/<your_config>.toml

**What happens:**

1. The GUI opens for manual validation of frozen well counts
2. After validation, temperature-binned frozen well counts are created
3. INP/L concentrations are calculated with Agresti-Coull confidence intervals

**Output files** (in the experiment folder):

- ``reviewed_*.dat`` -- Original data with GUI corrections
- ``frozen_at_temp_reviewed_*.csv`` -- Frozen wells binned to 0.5 deg C intervals
- ``INPs_L_frozen_at_temp_reviewed_*.csv`` -- INP concentrations per liter
- ``plot_*_INPs_L_*.png`` -- (optional) INP spectrum plot

Stage 2: Blank Correction (``main_for_blanks.py``)
----------------------------------------------------

This stage averages blank measurements and subtracts them from experimental data
with proper error propagation.

**Configuration:**

Copy ``configs/templates/blanks.example.toml`` into your campaign folder
(``configs/<CAMPAIGN>/blanks/``) and edit the values:

.. code-block:: toml

   project_folder = "data/your_project"
   blank_includes = ["INPs_L_frozen_at_temp_reviewed", "blank"]
   blank_excludes = []
   sample_excludes = ["05.22.25"]        # dates/folders to skip
   multiple_per_day = true               # use all blanks per day, or only the latest
   only_within_dates = false             # only correct samples within the blank date range
   show_comp_plot = true                 # pre/post correction comparison plot

**Running:**

.. code-block:: bash

   python -m olaf.main_for_blanks configs/<CAMPAIGN>/blanks/blanks.toml

**Output files:**

- ``combined_blank_YYYY-MM-DD_YYYY-MM-DD.csv`` -- Averaged blank data (project folder)
- ``blank_corrected_*_INPs_L_*.csv`` -- Corrected INP concentrations (each experiment folder)
- ``blank_corrected_comp_plot_*.png`` -- (optional) Pre/post correction comparison

Stage 3: Final File Generation (``main_final_combine.py``)
-----------------------------------------------------------

This stage combines multiple treatments from the same sampling date into a single
ARM-format CSV file.

**Configuration:**

Copy ``configs/templates/final_combine.example.toml`` into your campaign folder
(``configs/<CAMPAIGN>/final_combine/``) and edit the values:

.. code-block:: toml

   project_folder = "data/your_project"
   includes = ["INPs_L", "frozen_at_temp", "reviewed", "blank_corrected", "10%"]
   excludes = ["blanks"]

   # ARM header metadata (arm_mentor, contact, data_description, ...) also live here.

   # Maps each treatment name to its integer flag in the ARM output.
   # Keep this table LAST: a [table] header captures every key below it.
   [treatment_dict]
   base = 0
   heat = 1
   peroxide = 2

**Running:**

.. code-block:: bash

   python -m olaf.main_final_combine configs/<CAMPAIGN>/final_combine/final_combine.toml

**Output files** (in ``final_files/`` subdirectory):

- ``project_name_YYYY-MM-DD_HHMMSS.csv`` -- ARM-format combined data


Data File Requirements
-----------------------

OLAF expects experiment data organized as:

.. code-block:: text

   data/your_experiment_MM.DD.YYYY/
   ├── experiment_name.dat       # Tab-delimited INS data
   └── dat_Images/               # Microscope images
       ├── image_001.png
       ├── image_002.png
       └── ...

The ``.dat`` file must contain these columns:

- ``Time`` -- Timestamp
- ``Avg_Temp`` -- Average temperature reading
- ``Sample_0`` through ``Sample_N`` -- Frozen well counts per sample
- ``Picture`` -- Reference to corresponding microscope image
