"""Stage 1: process raw freezing data into temperature-binned counts and INPs/L.

Configuration lives in a ``.toml`` file (see ``configs/templates/main.example.toml``).
Either edit ``DEFAULT_CONFIG`` below or pass a config path on the command line:

    python -m olaf.main configs/<CAMPAIGN>/main-process/<your_config>.toml
"""

import tkinter as tk

from olaf.config import MainConfig, load_config, resolve_config_path, save_copy
from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.di_background import resolve_di_background
from olaf.processing.graph_data_csv import DEFAULT_EXCLUDES as GRAPH_EXCLUDES
from olaf.processing.graph_data_csv import GraphDataCSV
from olaf.processing.spaced_temp_csv import DEFAULT_EXCLUDES as SPACED_EXCLUDES
from olaf.processing.spaced_temp_csv import SpacedTempCSV

# -----------------------------    CONFIG    ----------------------------------------
# Default config used when no path is given on the command line.
DEFAULT_CONFIG = "configs/RAM_CINC/main-process/A12_07.16.25_base.toml"


def run(config: MainConfig) -> None:
    """Run stage 1 processing for a single experiment described by ``config``."""
    treatment = tuple(config.treatment)
    # A cold-plate plate has no DI column, so its background comes from separate .dat
    # files. Resolve those first: a missing DI review should surface before the
    # researcher works through the sample images.
    di_excludes: tuple[str, ...] = ()
    di_background = None
    if config.is_cold_plate:
        di_excludes = tuple(path.stem for path in config.resolved_di_files)
        di_background = resolve_di_background(config)
        print(f"cold-plate DI background: {di_background}")

    window = tk.Tk()
    try:
        FreezingReviewer(
            window,
            config.data_folder,
            config.num_samples,
            config.wells_per_sample,
            config.dict_samples_to_dilution,
            includes=treatment,
            excludes=di_excludes,
        )
        window.mainloop()
    finally:
        # The review ends with quit(), which leaves tkinter._default_root pointing here.
        window.destroy()

    # Processing to create the temperature-binned .csv file
    spaced_temp_csv = SpacedTempCSV(
        config.data_folder,
        config.num_samples,
        includes=treatment,
        excludes=(*SPACED_EXCLUDES, *di_excludes),
    )
    spaced_temp_csv.create_temp_csv(
        config.dict_samples_to_dilution,
        config.freezing_point_depression_dict,
        config.wells_per_sample,
        config.sample_type,
    )

    if di_background is not None:
        # Out of scope means stop, not fall through. GraphDataCSV reads the background from
        # the `inf` dilution column, which a cold-plate plate does not have; carrying on
        # would either crash deep in the maths or, worse, quietly substitute a real sample
        # column for the DI and write a plausible-looking INPs_L file.
        raise NotImplementedError(
            "Cold-plate stage 1 stops after binning: the INP calculation still reads its "
            "background from the `inf` dilution column and is not wired to the DI file yet. "
            f"The DI background is ready at {di_background}."
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
            excludes=(*GRAPH_EXCLUDES, *di_excludes),
        )
        graph_data_csv.convert_INPs_L(header, show_plot=True)


if __name__ == "__main__":
    config_path = resolve_config_path(DEFAULT_CONFIG)
    config = load_config(config_path, MainConfig)
    try:
        run(config)
    finally:
        # A cold-plate run stops early by design, and a crash can still leave reviewed and
        # binned files behind. Those are the cases where the inputs are hardest to
        # reconstruct later, so record the config whatever happened.
        save_copy(config_path, config.data_folder, config.provenance_stem())
