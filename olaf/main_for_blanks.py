"""Stage 2: apply blank corrections to the stage-1 INPs/L outputs.

Configuration lives in a ``.toml`` file (see ``configs/templates/blanks.example.toml``).
Either edit ``DEFAULT_CONFIG`` below or pass a config path on the command line:

    python -m olaf.main_for_blanks configs/<CAMPAIGN>/blanks/blanks.toml
"""

from olaf.config import BlankConfig, load_config, resolve_config_path, save_provenance_copy
from olaf.processing.blank_correction import BlankCorrector

# -----------------------------    CONFIG    ----------------------------------------
# Default config used when no path is given on the command line.
DEFAULT_CONFIG = "configs/RAM_CINC/blanks/blanks.toml"


def run(config: BlankConfig) -> None:
    """Find and average blanks, then apply them to the samples described by ``config``."""
    corrector = BlankCorrector(
        config.project_folder,
        tuple(config.blank_includes),
        tuple(config.blank_excludes),
        tuple(config.sample_excludes),
        multiple_per_day=config.multiple_per_day,
    )
    corrector.average_blanks()
    corrector.apply_blanks(
        only_within_dates=config.only_within_dates,
        show_comp_plot=config.show_comp_plot,
    )


if __name__ == "__main__":
    config_path = resolve_config_path(DEFAULT_CONFIG)
    config = load_config(config_path, BlankConfig)
    run(config)
    save_provenance_copy(config_path, config.project_folder, config.provenance_stem())
