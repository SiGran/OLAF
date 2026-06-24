"""Stage 3: combine treatments into ARM-format final files.

Configuration lives in a ``.toml`` file (see
``configs/templates/final_combine.example.toml``). Either edit ``DEFAULT_CONFIG`` below or
pass a config path on the command line:

    python -m olaf.main_final_combine configs/<CAMPAIGN>/final_combine/final_combine.toml
"""

from olaf.config import (
    FinalCombineConfig,
    load_config,
    resolve_config_path,
    save_provenance_copy,
)
from olaf.processing.final_file_creation import FinalFileCreation

# -----------------------------    CONFIG    ----------------------------------------
# Default config used when no path is given on the command line.
DEFAULT_CONFIG = "configs/RAM_CINC/final_combine/final_combine.toml"


def run(config: FinalCombineConfig) -> None:
    """Create all ARM-format final files for the project described by ``config``."""
    to_final_file = FinalFileCreation(
        config.project_folder,
        tuple(config.includes),
        tuple(config.excludes),
    )
    to_final_file.create_all_final_files(config.treatment_dict, config.build_header_start())


if __name__ == "__main__":
    config_path = resolve_config_path(DEFAULT_CONFIG)
    config = load_config(config_path, FinalCombineConfig)
    run(config)
    save_provenance_copy(
        config_path, config.project_folder / "final_files", config.provenance_stem()
    )
