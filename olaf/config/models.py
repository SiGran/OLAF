"""Pydantic models describing the configuration for each OLAF pipeline stage.

Each model maps one-to-one onto the user inputs that used to live at the top of the
corresponding ``main_*.py`` script. Configuration is now supplied through a ``.toml`` file
(see ``configs/templates/``) so that the scripts themselves no longer need to be edited and
a copy of the exact inputs can be stored alongside the generated output.
"""

from __future__ import annotations

import re
import warnings
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from olaf.CONSTANTS import DATE_PATTERN, ERROR_SIGNAL


def sanitize_for_filename(value: str) -> str:
    """Make ``value`` safe to use as part of a filename.

    Replaces path separators, whitespace and other awkward characters with underscores and
    collapses repeats, so the result is portable across operating systems.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("_") or "config"


class MainConfig(BaseModel):
    """Configuration for stage 1 processing (``main.py``)."""

    model_config = ConfigDict(extra="forbid")

    # Core experiment description
    data_folder: Path
    site: str
    start_time: str
    end_time: str
    filter_color: str
    notes: str
    user: str
    IS: str
    num_samples: int
    sample_type: str = "air"
    vol_air_filt: float = Field(default=1.0, gt=0.0)  # L; divides INP/L, must be positive
    wells_per_sample: int
    proportion_filter_used: float = Field(default=1.0, gt=0.0, le=1.0)
    vol_susp: float = 10.0
    treatment: list[str] = Field(default_factory=lambda: ["base"])
    dict_samples_to_dilution: dict[str, float]

    # Optional / conditional inputs
    # lower_altitude: float = 0.0  # m agl, only used for TBS sites
    # upper_altitude: float = 0.0  # m agl, only used for TBS sites
    # dry_mass: float = 1.0  # g, only used when sample_type is soil
    optional: dict[str,float] = Field(default_factory=dict)
    freezing_point_depression_dict: dict[str, float] = Field(default_factory=dict)

    @field_validator("treatment", mode="before")
    @classmethod
    def _coerce_treatment(cls, value: object) -> object:
        """Allow a single treatment string in addition to a list."""
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def _warn_on_soft_mismatches(self) -> MainConfig:
        """Reproduce the non-fatal sanity warnings from the original main.py."""
        if not all(str(t) in str(self.data_folder) for t in self.treatment):
            warnings.warn(
                f"your selection for treatment: {tuple(self.treatment)} does not match with the "
                f"specified folder: {self.data_folder.name}",
                stacklevel=2,
            )
        if self.num_samples * self.wells_per_sample != 192:
            warnings.warn(
                f"Number of samples * wells per sample "
                f"({self.num_samples}*{self.wells_per_sample}) is not equal to 192",
                stacklevel=2,
            )
        return self

    @property
    def effective_vol_air_filt(self) -> float:
        """Volume of air filtered after applying the automatic blank/soil adjustments."""
        vol_air_filt = self.vol_air_filt
        if "blank" in self.treatment or self.sample_type != "air":
            vol_air_filt = 1  # Always the case for blank
        if "soil" in self.sample_type:
            vol_air_filt = self.vol_susp / self.optional["dry_mass"]
        return vol_air_filt

    def to_header(self) -> str:
        """Assemble the CSV header string written into the stage-1 output files."""
        header = (
            f"site = {self.site}\nstart_time = {self.start_time}\nend_time = {self.end_time}\n"
            f"filter_color = {self.filter_color}\nsample_type = {self.sample_type}\n"
            f"vol_air_filt = {self.effective_vol_air_filt}\n"
            f"proportion_filter_used = {self.proportion_filter_used}\n"
            f"vol_susp = {self.vol_susp}\ntreatment = {self.treatment[0]}\nnotes = {self.notes}\n"
            f"user = {self.user}\nIS = {self.IS}\n"
        )
        if "TBS" in self.site:
            header += (
                f"lower_altitude = {self.optional['lower_altitude']}\n"
                f"upper_altitude = {self.optional['upper_altitude']}\n"
            )
        return header

    def check_dates(self) -> list[str]:
        """Return the dates found in the folder name, warning on any start_time mismatch."""
        found_dates = re.findall(DATE_PATTERN, self.data_folder.name)
        if not found_dates:
            warnings.warn("No date found in folder name", stacklevel=2)
        start_time_obj = datetime.strptime(self.start_time.strip(), "%Y-%m-%d %H:%M:%S")
        valid_dates = []
        for date in found_dates:
            date_obj = datetime.strptime(date, "%m.%d.%y")
            if date_obj.date() != start_time_obj.date():
                warnings.warn(
                    f"Date {date} does not match with the specified start time: {self.start_time}",
                    stacklevel=2,
                )
                continue
            valid_dates.append(date)
        return valid_dates

    def provenance_stem(self) -> str:
        """Filename stem encoding the crucial variables: site, start date and treatment."""
        date = self.start_time.strip()[:10]
        treatment = self.treatment[0] if self.treatment else "unknown"
        return sanitize_for_filename(f"{self.site}_{date}_{treatment}")


class BlankConfig(BaseModel):
    """Configuration for stage 2 blank correction (``main_for_blanks.py``)."""

    model_config = ConfigDict(extra="forbid")

    project_folder: Path
    blank_includes: list[str] = Field(
        default_factory=lambda: ["INPs_L_frozen_at_temp_reviewed", "blank"]
    )
    blank_excludes: list[str] = Field(default_factory=list)
    sample_excludes: list[str] = Field(default_factory=list)
    multiple_per_day: bool = False
    only_within_dates: bool = True
    show_comp_plot: bool = False

    def provenance_stem(self) -> str:
        """Filename stem encoding the crucial variable: the project folder name."""
        return sanitize_for_filename(f"{self.project_folder.name}_blank_correction")


class FinalCombineConfig(BaseModel):
    """Configuration for stage 3 final file creation (``main_final_combine.py``)."""

    model_config = ConfigDict(extra="forbid")

    project_folder: Path
    includes: list[str] = Field(
        default_factory=lambda: [
            "INPs_L",
            "frozen_at_temp",
            "reviewed",
            "blank_corrected",
            "10%",
        ]
    )
    excludes: list[str] = Field(default_factory=lambda: ["blanks"])
    treatment_dict: dict[str, int] = Field(
        default_factory=lambda: {"base": 0, "heat": 1, "peroxide": 2}
    )

    # ARM header metadata. Kept as structured fields so the boilerplate header can be
    # rebuilt in code (with ERROR_SIGNAL injected from CONSTANTS). A fully custom header
    # can be supplied via ``header_start`` to override the generated one.
    arm_mentor: str = "Jessie Creamean at Colorado State University"
    contact: str = "Jessie.Creamean@colostate.edu; cchume@rams.colostate.edu"
    data_description: str = (
        "Number of ice nucleating particles per L of air at STP (0 degC and 101.325 kPa); "
        "lower 95 percent confidence limit; upper 95 percent confidence limit"
    )
    metadata_url: str = "https://docs.arm.gov/share/s/BkJRSN5mR1mcZKjZm13Vtw"
    treatment_flags_description: str = "0 = untreated; 1 = heat treated; and 2 = peroxide treated"
    qc_flag_description: str = (
        "0 = no correction applied; 1 = correction applied. "
        "For more details visit: doi.org/10.5194/essd-17-6943-2025"
    )
    header_start: str | None = None

    def build_header_start(self) -> str:
        """Return the explicit header override, or build one from the structured fields."""
        if self.header_start is not None:
            return self.header_start
        return (
            f"ARM Mentor: {self.arm_mentor}\n"
            f"Contact: {self.contact}\n"
            f"Data: {self.data_description}\n"
            f"For access to all filter metadata (e.g. flows times sites notes etc.) visit "
            f"{self.metadata_url}\n"
            f"Treatment flags: {self.treatment_flags_description}\n"
            f"QC flag: {self.qc_flag_description}\n"
            f"Missing values or values below detection limit are denoted as {ERROR_SIGNAL}\n"
        )

    def provenance_stem(self) -> str:
        """Filename stem encoding the crucial variable: the project folder name."""
        return sanitize_for_filename(f"{self.project_folder.name}_final_combine")
