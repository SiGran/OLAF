"""Helpers for locating, loading, and recording OLAF configuration files.

The pipeline scripts each expose an editable ``DEFAULT_CONFIG`` path and also accept a
config path on the command line. ``resolve_config_path`` implements that "CLI overrides the
default" behaviour, ``load_config`` parses and validates a ``.toml`` file into a pydantic
model, and ``save_copy`` records the exact config used next to the output.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tomllib
import warnings
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

ConfigT = TypeVar("ConfigT", bound=BaseModel)


def resolve_config_path(default: str | Path, argv: list[str] | None = None) -> Path:
    """Resolve which config file to use.

    A path supplied on the command line takes precedence; otherwise the script's editable
    ``default`` is used.

    Args:
        default: Fallback config path defined in the calling script.
        argv: Optional argument list (defaults to ``sys.argv[1:]``), mainly for testing.

    Returns:
        The resolved path to the configuration file.
    """
    parser = argparse.ArgumentParser(
        description="Run an OLAF pipeline stage using a .toml configuration file."
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=None,
        help="Path to the .toml config file. Overrides the DEFAULT_CONFIG set in the script.",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    return Path(args.config) if args.config else Path(default)


def load_config(path: str | Path, model_cls: type[ConfigT]) -> ConfigT:
    """Load and validate a ``.toml`` configuration file into the given model.

    Args:
        path: Path to the ``.toml`` configuration file.
        model_cls: The pydantic model class to validate the data against.

    Returns:
        A validated instance of ``model_cls``.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the file cannot be parsed or fails validation (with a readable message).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"Could not parse TOML config {path}: {exc}") from exc

    try:
        return model_cls(**data)
    except ValidationError as exc:
        raise ValueError(_validation_message(path, model_cls, data, exc)) from exc


def _validation_message(
    path: Path,
    model_cls: type[BaseModel],
    data: dict[str, object],
    exc: ValidationError,
) -> str:
    """Build a readable error for a config that failed validation.

    Beyond pydantic's own report, this names the stage the caller expected and — when the
    file clearly belongs to a different stage — the command that would run it correctly.
    Running a stage's script against another stage's config is easy to do and otherwise
    surfaces only as a list of "Extra inputs are not permitted" errors.
    """
    from olaf.config.models import detect_stage, stage_for_dir, stage_for_model

    lines = [f"Invalid configuration in {path}:"]

    expected = stage_for_model(model_cls)
    if expected is not None:
        lines.append(
            f"Expected a stage {expected.number} ({expected.name}) config for "
            f"{model_cls.__name__}, normally found in {expected.config_dir}/."
        )

    actual = detect_stage(data) or stage_for_dir(path.parent.name)
    if actual is not None and actual.model is not model_cls:
        lines.append(
            f"This file looks like a stage {actual.number} ({actual.name}) config. "
            f"Run it with:\n    python -m {actual.script} {path}"
        )

    moved_keys = {"dry_mass", "lower_altitude", "upper_altitude"}
    extra_keys = {
        str(err["loc"][0])
        for err in exc.errors()
        if err["type"] == "extra_forbidden" and err["loc"]
    }
    if extra_keys & moved_keys:
        lines.append(
            f"Note: {sorted(extra_keys & moved_keys)} moved into the [optional] table — "
            "see configs/templates/main.example.toml."
        )

    lines.append(str(exc))
    return "\n".join(lines)


def save_copy(
    config_path: str | Path, output_dir: str | Path, name: str | None = None
) -> Path | None:
    """Copy the config file into ``output_dir`` so the run's inputs are recorded with its output.

    The copy is prefixed with ``used_config_`` to make it easy to spot. When ``name`` is
    given, it is used as the filename stem (e.g. crucial variables such as site/date/
    treatment) instead of the original config's name. Existing copies are not overwritten
    silently; a numeric suffix is appended instead.

    Args:
        config_path: The configuration file that was used for the run.
        output_dir: The directory where the run wrote its output.
        name: Optional filename stem encoding the crucial variables of the run. Defaults to
            the original config file's stem.

    Returns:
        The path of the written copy, or ``None`` if the output directory does not exist.
    """
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        warnings.warn(
            f"output directory {output_dir} does not exist; no used_config_* provenance "
            "copy was written for this run",
            stacklevel=2,
        )
        return None

    stem = name if name else config_path.stem
    suffix = config_path.suffix or ".toml"
    target = output_dir / f"used_config_{stem}{suffix}"
    counter = 1
    while target.exists():
        target = output_dir / f"used_config_{stem}({counter}){suffix}"
        counter += 1

    shutil.copy2(config_path, target)
    return target
