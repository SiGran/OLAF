"""Resolve the DI (deionized water) background for a cold-plate run.

On an ice spectrometer the DI background is a column *inside* the sample plate: the
``inf`` entry in ``dict_samples_to_dilution``. A cold-plate sample plate has no such
column, so the background comes from one or more separate ``.dat`` files sitting in the
same data folder, named in the stage-1 config as ``di_files``.

Each DI ``.dat`` has to travel the same road as a sample: researcher review in the GUI,
then temperature binning into a ``frozen_at_temp_*.csv``. This module does only the work
that is still missing — a DI that already has its ``frozen_at_temp`` file is left alone
and never reopens the GUI — and then combines the per-run files into one DI spectrum
according to ``di_combined``.

The combined file is written with a metadata header, so read it back with
:func:`olaf.utils.df_utils.read_with_flexible_header` rather than a bare ``pd.read_csv``.
"""

from __future__ import annotations

import glob as _glob
import re
import tkinter as tk
import warnings
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from olaf.CONSTANTS import DATE_PATTERN
from olaf.image_verification.freezing_reviewer import FreezingReviewer
from olaf.processing.spaced_temp_csv import SpacedTempCSV
from olaf.utils.path_utils import find_latest_file, save_df_file

if TYPE_CHECKING:
    from olaf.config import MainConfig

COMBINED_PREFIX = "combined_DI"
SOURCE_SEPARATOR = "; "
# DI is pure water; this picks SpacedTempCSV's no-depression binning path.
DI_SAMPLE_TYPE = "air"


def _match_versions(folder: Path, base_pattern: str) -> list[Path]:
    """Files matching ``base_pattern`` exactly, plus its ``(N)`` versions — nothing longer.

    A plain trailing ``*`` would let one name swallow another that merely starts the same
    way: ``combined_DI_avg_07.16.25`` would match ``combined_DI_avg_07.16.25_07.17.25.csv``,
    a different DI set entirely.
    """
    return sorted(
        set(folder.glob(f"{base_pattern}.csv")) | set(folder.glob(f"{base_pattern}([0-9]*).csv"))
    )


def _next_free_path(path: Path) -> Path:
    """``path``, or the first ``(N)`` variant that does not exist yet."""
    counter = 0
    stem = path.stem
    while path.exists():
        counter += 1
        path = path.with_name(f"{stem}({counter}){path.suffix}")
    return path


def find_frozen_at_temp(di_dat: Path) -> Path | None:
    """Return the ``frozen_at_temp`` csv already binned for ``di_dat``, if there is one.

    ``SpacedTempCSV`` saves as ``frozen_at_temp_{stem}.csv`` where the stem belongs to the
    *reviewed* ``.dat``, so the name picks up a ``reviewed_`` infix along the way. The
    leading wildcard absorbs it; ``find_latest_file`` resolves ``(N)`` versions.
    """
    matches = _match_versions(di_dat.parent, f"frozen_at_temp_*{_glob.escape(di_dat.stem)}")
    if not matches:
        return None
    return find_latest_file(matches) if len(matches) > 1 else matches[0]


def ensure_frozen_at_temp(di_dat: Path, config: MainConfig) -> Path:
    """Return ``di_dat``'s ``frozen_at_temp`` csv, reviewing and binning it if missing.

    Opens the GUI only when the csv is genuinely absent, so re-running a cold-plate
    experiment does not make the researcher review the same DI plate twice.
    """
    existing = find_frozen_at_temp(di_dat)
    if existing is not None:
        print(f"DI {di_dat.name}: using existing {existing.name}")
        return existing

    print(f"DI {di_dat.name}: no frozen_at_temp file yet, opening review")
    # Pin every lookup to this one file: DataHandler matches on substrings, so without the
    # stem it would happily pick up a sample .dat from the same folder.
    includes = (di_dat.stem,)

    window = tk.Tk()
    FreezingReviewer(
        window,
        di_dat.parent,
        config.num_samples,
        config.wells_per_sample,
        config.dict_samples_to_dilution,
        includes=includes,
    )
    window.mainloop()

    spaced_temp_csv = SpacedTempCSV(di_dat.parent, config.num_samples, includes=includes)
    # Deionized water has no solute, so no freezing point depression: bin the DI plate on
    # the pure-water path rather than shifting its temperature axis by the *sample* plate's
    # correction, which for a salt run displaces it by up to 2 degC.
    spaced_temp_csv.create_temp_csv(
        config.dict_samples_to_dilution,
        {},
        config.wells_per_sample,
        DI_SAMPLE_TYPE,
    )

    created = find_frozen_at_temp(di_dat)
    if created is None:
        raise FileNotFoundError(
            f"No frozen_at_temp csv was produced for DI file {di_dat}. The review may have "
            "been closed before the last image was confirmed."
        )
    return created


def di_dates(di_files: list[Path]) -> str:
    """The date tag identifying this DI set, taken from the DI filenames."""
    found: list[str] = []
    for path in di_files:
        found.extend(re.findall(DATE_PATTERN, path.name))
    unique = sorted(set(found), key=lambda d: datetime.strptime(d, "%m.%d.%y"))
    if not unique:
        warnings.warn(
            f"No date found in DI filenames {[p.name for p in di_files]}; "
            "the combined DI file will be tagged 'unknown'",
            stacklevel=2,
        )
        return "unknown"
    return "_".join(unique)


def combined_path(data_folder: Path, method: str, date: str) -> Path:
    """Where the combined DI file for this set and combination method lives."""
    return data_folder / f"{COMBINED_PREFIX}_{method}_{date}.csv"


def find_combined(data_folder: Path, method: str, date: str) -> Path | None:
    """Return an already-written combined DI file for this set and method, if any."""
    exact = combined_path(data_folder, method, date)
    matches = _match_versions(data_folder, _glob.escape(exact.stem))
    if not matches:
        return None
    return find_latest_file(matches) if len(matches) > 1 else matches[0]


def _combined_sources(path: Path) -> list[str]:
    """The ``di_source_files`` recorded in an existing combined DI file's header."""
    with open(path) as f:
        for line in f:
            if line.startswith("degC,"):
                break
            key, _, value = line.partition(" = ")
            if key.strip() == "di_source_files":
                return [name.strip() for name in value.strip().split(SOURCE_SEPARATOR)]
    return []


def _reusable_combined(
    data_folder: Path, method: str, date: str, frozen_csvs: list[Path]
) -> Path | None:
    """An existing combined file for this set, but only if it was built from these inputs.

    The filename records the method and the date, not which runs went in. Re-reviewing a DI
    plate produces a ``(N)`` version and changing ``di_files`` keeps the same date, so
    matching on the name alone would silently hand back a stale background.
    """
    existing = find_combined(data_folder, method, date)
    if existing is None:
        return None
    wanted = [path.name for path in frozen_csvs]
    recorded = _combined_sources(existing)
    if recorded != wanted:
        warnings.warn(
            f"{existing.name} was built from {recorded or 'unrecorded inputs'}, but this run "
            f"uses {wanted}; writing a new combined DI file rather than reusing it",
            stacklevel=2,
        )
        return None
    print(f"Using existing combined DI file: {existing.name}")
    return existing


def _read_di_frames(frozen_csvs: list[Path]) -> tuple[list[pd.DataFrame], list[str]]:
    """Read the per-run files, checking they describe the same plate layout."""
    frames = [pd.read_csv(path) for path in frozen_csvs]
    column_sets = []
    for path, frame in zip(frozen_csvs, frames, strict=True):
        sample_cols = [col for col in frame.columns if col.startswith("Sample_")]
        if not sample_cols:
            raise ValueError(f"No Sample_* columns found in DI file {path.name}")
        if "degC" not in frame.columns:
            raise ValueError(f"No degC column found in DI file {path.name}")
        column_sets.append(tuple(sorted(sample_cols)))
    if len(set(column_sets)) > 1:
        # Left alone, pd.concat would NaN-fill the gaps: "sum" would then read a missing
        # column as zero frozen wells (a DI biased low) and "avg" would die in the int cast.
        detail = ", ".join(
            f"{path.name}: {list(cols)}"
            for path, cols in zip(frozen_csvs, column_sets, strict=True)
        )
        raise ValueError(f"DI files do not share the same Sample_* columns — {detail}")
    return frames, list(column_sets[0])


def _align_di_frames(
    frames: list[pd.DataFrame], sample_cols: list[str]
) -> tuple[list[pd.DataFrame], pd.Series]:
    """Put every run on one temperature axis, warm to cold, carrying values forward.

    ``SpacedTempCSV`` writes one off-grid row per run — the first-frozen temperature,
    rounded to 0.1 rather than snapped to ``TEMP_STEP`` (``spaced_temp_csv.py``, and the
    0.5-grid filter afterwards only runs for salt/sea water). Two runs therefore land their
    off-grid rows in different places, and grouping the raw union would leave each of those
    bins fed by one run while its neighbours are fed by all of them. That makes the combined
    spectrum go *down* as the plate gets colder, which is physically impossible and breaks
    the monotonicity the GUI enforces on every run.

    Reindexing each run onto the shared axis and forward-filling from the warmer side fixes
    it: a run that has no row at exactly this temperature still had its last count standing.
    Bins warmer than a run's own first row are zero — nothing had frozen yet.
    """
    axis = sorted({float(value) for frame in frames for value in frame["degC"]}, reverse=True)
    index = pd.Index(axis, name="degC")

    aligned = []
    coverage = pd.Series(0, index=index, dtype="int64")
    for frame in frames:
        run = frame.set_index("degC")[sample_cols].sort_index(ascending=False)
        aligned.append(run.reindex(index).ffill().fillna(0))
        covered = (index <= run.index.max()) & (index >= run.index.min())
        coverage += pd.Series(covered.astype("int64"), index=index)
    return aligned, coverage


def _check_monotonic(clean_df: pd.DataFrame, sample_cols: list[str]) -> None:
    """Frozen wells may never decrease as the temperature falls."""
    for col in sample_cols:
        values = clean_df[col].to_numpy()
        if (np.diff(values) < 0).any():
            bad = int(np.argmax(np.diff(values) < 0))
            raise ValueError(
                f"Combined DI is not monotonic in {col}: {values[bad]} frozen wells at "
                f"{clean_df['degC'].iloc[bad]} degC drops to {values[bad + 1]} at "
                f"{clean_df['degC'].iloc[bad + 1]} degC"
            )


def combine_di(
    frozen_csvs: list[Path],
    method: str,
    data_folder: Path,
    date: str,
    wells_per_sample: int,
) -> Path:
    """Combine per-run DI ``frozen_at_temp`` files into one DI spectrum.

    ``avg`` takes the mean frozen well count per temperature bin, ``sum`` the total, and
    ``single`` passes the one run through. All three write a file with the same schema, so
    callers do not have to branch on the method.

    Two bookkeeping columns come along, because a frozen well count means nothing without
    the plate it came from. ``di_wells`` is the pooled well total behind that row: under
    ``sum`` the counts add while a single plate's ``wells_per_sample`` does not, so this is
    the only record of the real denominator — read it, do not assume ``wells_per_sample``.
    ``di_count`` is how many runs actually *measured* the bin; where it is below the run
    count, the remaining runs were carried forward from their last measured temperature.
    """
    if method not in {"avg", "sum", "single"}:
        raise ValueError(f'Unknown di_combined method "{method}"; expected avg, sum or single')
    if method == "single" and len(frozen_csvs) != 1:
        raise ValueError(
            f'di_combined = "single" needs exactly one DI file, got {len(frozen_csvs)}'
        )

    existing = _reusable_combined(data_folder, method, date, frozen_csvs)
    if existing is not None:
        return existing

    frames, sample_cols = _read_di_frames(frozen_csvs)
    aligned, coverage = _align_di_frames(frames, sample_cols)

    stacked = pd.concat(aligned)
    grouped = stacked.groupby(level="degC", sort=False)[sample_cols]
    if method == "sum":
        clean_df = grouped.sum()
        # Every run contributes a value at every bin after the forward fill, including the
        # bins it never reached itself, so the whole pool is behind every row. Keying this
        # on `coverage` instead would claim one plate's denominator for a summed count.
        di_wells = pd.Series(len(frames) * wells_per_sample, index=coverage.index, dtype="int64")
    else:  # "avg" and "single" both keep one plate's denominator
        # Round half up. numpy's round() is half-to-even, and two runs one well apart land
        # on .5 as a matter of course, so half-to-even would bias alternate bins. Well
        # counts are never negative, so the truncating cast below is a floor.
        clean_df = grouped.mean() + 0.5
        di_wells = pd.Series(wells_per_sample, index=coverage.index, dtype="int64")

    clean_df = clean_df.astype("int64").sort_index(ascending=False)
    clean_df["di_count"] = coverage
    clean_df["di_wells"] = di_wells
    clean_df = clean_df.reset_index()
    _check_monotonic(clean_df, sample_cols)

    header_info = {
        "di_combined": method,
        "di_date": date,
        "di_runs": len(frozen_csvs),
        "wells_per_sample": wells_per_sample,
        "di_source_files": SOURCE_SEPARATOR.join(path.name for path in frozen_csvs),
    }
    # save_df_file versions a colliding name internally but returns None, so resolve the
    # free path here — otherwise this would hand back the path of the *older* file.
    save_file = _next_free_path(combined_path(data_folder, method, date))
    save_df_file(clean_df, save_file, header_info, index=False)
    print(f"Wrote combined DI file: {save_file.name}")
    return save_file


def resolve_di_background(config: MainConfig) -> Path:
    """Full cold-plate DI resolution: review what is missing, then combine.

    Returns the path to the DI spectrum this run should use as its background.
    """
    di_files = config.resolved_di_files
    frozen_csvs = [ensure_frozen_at_temp(path, config) for path in di_files]
    date = di_dates(di_files)
    method = config.di_combined or "single"
    return combine_di(frozen_csvs, method, config.data_folder, date, config.wells_per_sample)
