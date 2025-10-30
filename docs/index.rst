OLAF Documentation
==================

**OLAF** (OpenSource Library for Automating Freezing data acquisition from Ice Nucleation Spectrometer)
is a Python package for processing and analyzing Ice Nucleating Particle (INP) data from
Ice Nucleation Spectrometer (INS) experiments.

Overview
--------

OLAF automates the quantification of Ice Nucleating Particles (INPs) - aerosol particles
that trigger ice formation in clouds at various temperatures. This is critical for
understanding cloud formation, precipitation, and climate processes.

Key Features
~~~~~~~~~~~~

* **Interactive GUI** for manual validation of frozen well counts
* **Statistical analysis** using Agresti-Coull confidence intervals
* **Blank correction** with automated background subtraction
* **ARM format output** for atmospheric research integration
* **Multi-treatment support** (base, heat, peroxide treatments)
* **Comprehensive data validation** with error checking

Quick Start
-----------

Installation
~~~~~~~~~~~~

OLAF uses `uv <https://docs.astral.sh/uv/>`_ for package management::

    # Clone the repository
    git clone https://github.com/SiGran/OLAF.git
    cd OLAF

    # Create virtual environment and install dependencies
    uv venv
    uv sync

See the `GitHub README <https://github.com/SiGran/OLAF>`_ for detailed installation
instructions for Windows, macOS, and Linux.

Basic Usage
~~~~~~~~~~~

OLAF provides three main processing scripts:

1. **main.py** - Process raw INS data and review images in GUI
2. **main_for_blanks.py** - Average blank data and apply corrections
3. **main_final_combine.py** - Combine treatments into ARM format

Example workflow::

    from pathlib import Path
    from olaf.processing.spaced_temp_csv import SpacedTempCSV
    from olaf.processing.graph_data_csv import GraphDataCSV

    # Process temperature-binned data
    processor = SpacedTempCSV(folder_path, num_samples=6)
    temp_csv = processor.create_temp_csv(dict_samples_to_dilution)

    # Calculate INPs per Liter
    calculator = GraphDataCSV(folder_path, num_samples=6)
    calculator.convert_INPs_L(header_info, show_plot=True)

User Guide
----------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   usage/workflow
   usage/gui
   usage/configuration

API Reference
-------------

Core Processing Modules
~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   olaf.processing.spaced_temp_csv
   olaf.processing.graph_data_csv
   olaf.processing.blank_correction
   olaf.processing.final_file_creation

Image Verification (GUI)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   olaf.image_verification.freezing_reviewer
   olaf.image_verification.button_handler
   olaf.image_verification.data_loader

Utility Functions
~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   olaf.utils.data_handler
   olaf.utils.math_utils
   olaf.utils.df_utils
   olaf.utils.path_utils
   olaf.utils.plot_utils
   olaf.utils.type_utils

Scientific Background
---------------------

INP Calculation Method
~~~~~~~~~~~~~~~~~~~~~~

OLAF calculates INP concentrations using the formula:

.. math::

   INP/mL = \\frac{-\\ln((D_x - E_x)/D_x)}{C_x/1000} \\times F_x

Where:
  * :math:`D_x` = total wells minus background
  * :math:`E_x` = number of frozen wells
  * :math:`C_x` = well volume (50 μL)
  * :math:`F_x` = dilution factor

Confidence intervals are calculated using the Agresti-Coull method for binomial proportions.

Contributing
------------

Contributions are welcome! Please see the `GitHub repository <https://github.com/SiGran/OLAF>`_
for development guidelines.

License
-------

OLAF is licensed under the AGPL-3.0 license.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

