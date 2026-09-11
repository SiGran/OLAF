"""Stage 1: process raw freezing data into temperature-binned counts and INPs/L.

Configuration lives in a ``.toml`` file (see ``configs/templates/main.example.toml``).
Either edit ``DEFAULT_CONFIG`` below or pass a config path on the command line:

    python -m olaf.main configs/<CAMPAIGN>/process/<your_config>.toml
"""

import tkinter as tk

from olaf.config import MainConfig, load_config, resolve_config_path, save_copy
from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.processing.spaced_temp_csv import SpacedTempCSV

# -----------------------------    CONFIG    ----------------------------------------
# Default config used when no path is given on the command line.
DEFAULT_CONFIG = "configs/RAM_CINC/process/A12_07.16.25_base.toml"


def run(config: MainConfig) -> None:
    """Run stage 1 processing for a single experiment described by ``config``."""
    treatment = tuple(config.treatment)

    window = tk.Tk()
    FreezingReviewer(
        window,
        config.data_folder,
        config.num_samples,
        config.wells_per_sample,
        config.dict_samples_to_dilution,
        includes=treatment,
    )
    window.mainloop()

    # Processing to create the temperature-binned .csv file
    spaced_temp_csv = SpacedTempCSV(config.data_folder, config.num_samples, includes=treatment)
    spaced_temp_csv.create_temp_csv(
        config.dict_samples_to_dilution,
        config.freezing_point_depression_dict,
        config.wells_per_sample,
        config.sample_type,
    )

    # Processing to create INPs/L for each date found in the folder name
    header = config.to_header()
    for date in config.check_dates():
        print(f"Processing data for: {config.site} {date}")
        includes = (date, *treatment)
        # TODO: make the changes work for sample_type see issue #18 on github
        graph_data_csv = GraphDataCSV(
            config.data_folder,
            config.num_samples,
            config.sample_type,
            config.effective_vol_air_filt,
            config.wells_per_sample,
            config.proportion_filter_used,
            config.vol_susp,
            config.dict_samples_to_dilution,
            includes=includes,
        )
        graph_data_csv.convert_INPs_L(header, show_plot=True)


if __name__ == "__main__":
    config_path = resolve_config_path(DEFAULT_CONFIG)
    config = load_config(config_path, MainConfig)
    run(config)
    save_copy(config_path, config.data_folder, config.provenance_stem())
