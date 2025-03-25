import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.CONSTANTS import DATE_PATTERN
from olaf.utils.path_utils import natural_sort_key


def read_with_flexible_header(
    file_path: Path,
    expected_columns: tuple = ("°C", "dilution", "INPS_L", "lower_CI", "upper_CI"),
    max_rows: int = 20,
):
    """ """
    header_found = False
    header_lines = []
    i = 0
    with open(file_path, "r") as f:
        while not header_found:
            line = f.readline()
            if not line:  # end of file
                print(f"No columns {expected_columns} found in {file_path}")
                break
            elif tuple(line.strip().split(",")) == expected_columns:
                skiprows = i
                header_found = True
            else:
                header_lines.append(line.strip())
            i += 1

    return header_lines, pd.read_csv(file_path, skiprows=skiprows)


def is_within_dates(dates, folder_name):
    """
    Check if the folder name contains a date that is within the given date range.

    Args:
        dates: Tuple of (start_date, end_date) in string format
        folder_name: String name of folder which might contain a date

    Returns:
        bool: True if folder date is in range, False otherwise
    """
    # Extract date from folder name
    date_match = re.findall(DATE_PATTERN, folder_name)
    if not date_match or len(date_match) != 1:
        return False

    folder_date_str = date_match[0]

    try:
        earliest_date, latest_date = dates

        # Convert all dates to datetime objects
        # For the range dates, take just the date part if they have time
        start_date_str = earliest_date.split()[0] if " " in earliest_date else earliest_date
        end_date_str = latest_date.split()[0] if " " in latest_date else latest_date

        # Convert to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        folder_date = datetime.strptime(folder_date_str, "%m.%d.%y")

        # Check if folder date is within range (inclusive)
        return start_date <= folder_date <= end_date

    except (ValueError, IndexError):
        # If any parsing fails, assume not in range
        return False


def unique_dilutions(series):
    """Convert dilution values to integers when possible"""
    unique_vals = series.unique()
    # Convert values to appropriate numeric types
    cleaned_vals = []
    for val in unique_vals:
        try:
            # First convert to float
            float_val = float(val)
            # Convert to int if it's a whole number
            if float_val.is_integer():
                cleaned_vals.append(int(float_val))
            else:
                cleaned_vals.append(float_val)
        except (ValueError, TypeError):
            # Keep as is if not convertible
            cleaned_vals.append(val)

    return tuple(sorted(cleaned_vals))


def rms(x):
    return np.sqrt(np.mean(np.square(x)))


class BlankCorrector:
    def __init__(self, project_folder: Path) -> None:
        self.project_folder = project_folder
        self.blank_files = self._find_blank_files()
        self.combined_blank: dict[tuple[str, str], pd.DataFrame] = {}

    def _find_blank_files(self):
        """Find all blank CSV files in the project structure, selecting only one file per date"""

        # First collect all potential blank files
        potential_blank_files = []
        for experiment_folder in self.project_folder.iterdir():
            if experiment_folder.is_dir() and "blanks" in experiment_folder.name.lower():
                for file_path in experiment_folder.rglob("INPs_L*.csv"):
                    potential_blank_files.append(file_path)

        # Group files by date
        files_by_date = defaultdict(list)

        for file_path in potential_blank_files:
            date_match = re.findall(DATE_PATTERN, file_path.name)
            if date_match and len(date_match) == 1:  # skip if more dates match
                date = date_match[0]
                # Find the trailing number if it exists
                number_match = re.search(r"(\d+)\.csv$", file_path.name)
                number = int(number_match.group(1)) if number_match else 0
                files_by_date[date].append((file_path, number))

        # Select the file with the highest trailing number for each date
        blank_files = []
        for date, files in files_by_date.items():
            # Sort by the number (second element of tuple) in descending order
            # TODO: make sure this works to get the newest file
            files.sort(key=lambda x: x[1], reverse=True)
            # Add the file path (first element of tuple) with highest number
            blank_files.append(files[0][0])
            # Print statement for which file we found:
            print(f" found {len(files)} blank files for date {date}: {files}")
        return blank_files

    def average_blanks(self, save=True):
        # TODO add a date selection option?
        """Average all blank files into a single CSV file by temperature"""
        all_data = []

        # Track header information
        earliest_date = None
        latest_date = None
        header_info = {}

        for file in self.blank_files:
            header_lines, df = read_with_flexible_header(file)
            # Parse dates from headers
            for line in header_lines:
                if line.startswith("start_time = "):
                    date_str = line.replace("start_time = ", "")
                    if earliest_date is None or date_str < earliest_date:
                        earliest_date = date_str
                elif line.startswith("end_time = "):
                    date_str = line.replace("end_time = ", "")
                    if latest_date is None or date_str > latest_date:
                        latest_date = date_str
                elif " = " in line:
                    key, value = line.split(" = ", 1)
                    # Keep track of other header values (use the last file's values)
                    header_info[key] = value

            all_data.append(df)

        # Combine all blank dataframes
        combined_df = pd.concat(all_data)

        # Group by temperature bins and calculate average INPS/L and other stats
        grouped_INPS = (
            combined_df.groupby("°C")
            .agg(
                {
                    "dilution": [unique_dilutions],
                    "INPS_L": ["mean", "count"],
                    "lower_CI": [rms],
                    "upper_CI": [rms],
                    # Add other fields as needed
                }
            )
            .sort_index(ascending=False)
        )

        # Start new df by using the index of the grouped df (temperature bins)
        clean_df = pd.DataFrame(index=grouped_INPS.index)

        # Add other columns
        clean_df["dilution"] = grouped_INPS[("dilution", "unique_dilutions")]
        clean_df["INPS_L"] = grouped_INPS[("INPS_L", "mean")]
        clean_df["lower_CI"] = grouped_INPS[("lower_CI", "rms")]
        clean_df["upper_CI"] = grouped_INPS[("upper_CI", "rms")]
        clean_df["blank_count"] = grouped_INPS[("INPS_L", "count")]

        if save:
            clean_df = self._save_combined_blanks(clean_df, header_info, earliest_date, latest_date)

        self.combined_blank[(earliest_date, latest_date)] = clean_df
        return clean_df

    def _save_combined_blanks(self, clean_df, header_info, earliest_date, latest_date):
        # Save the combined blank data to a CSV file
        output_file = (
            self.project_folder / f"combined_blank_{earliest_date[:10]}_{latest_date[:10]}.csv"
        )
        counter = 0
        output_stem = output_file.stem
        while output_file.exists():
            # If the file exists, append a number to the filename
            counter += 1
            output_file = output_file.with_name(output_stem + f"({counter})" + output_file.suffix)

        header_info["start_time"] = earliest_date
        header_info["end_time"] = latest_date

        with open(output_file, "w") as f:
            f.write(f"filename = {output_file.name}\n")
            for key, value in header_info.items():
                f.write(f"{key} = {value}\n")
            clean_df.to_csv(f, index=False)
        return clean_df

    def apply_blanks(self):
        """Apply the blank correction to all INPs/L files in the project folder"""

        for dates, df in self.combined_blank.items():
            df_correction = df
            for experiment_folder in self.project_folder.iterdir():
                if "blank" not in experiment_folder.name and is_within_dates(
                    dates, experiment_folder.name
                ):
                    # Collect all INPs/L files in the experiment folder
                    input_files = list(experiment_folder.rglob("INPs_L*.csv"))
                    # pick the one with the highest number (latest)
                    input_files = sorted(input_files, key=lambda x: natural_sort_key(str(x)))

                    # Process the latest INPS file (assumes one relevant per folder)
                    inps_file = input_files[-2]
                    header_lines, inps_df = read_with_flexible_header(inps_file)

                    # Check if the blank correction covers all temperatures from inps
                    inps_temps = inps_df["°C"]
                    blank_temps = df_correction.index.to_series()
                    missing_temps = set(inps_temps) - set(blank_temps)
                    if missing_temps:
                        # If missing temp higher than highest blank temp, extrapolate
                        if max(missing_temps) > max(blank_temps):
                            # Extrapolate the blank correction
                            blank_temps = self._extrapolate_blanks(missing_temps)
                            missing_temps = set(inps_temps) - set(blank_temps)
                        if min(missing_temps) < min(blank_temps):
                            print(f"Missing temperatures in blank correction: {missing_temps}")

                    # Apply the blank correction

                    # Root sum of squares for CI
                    # Iterate through all non-blank folders and apply the blank correction
                    """
                    All the Volume stuff
                    - Take the proportion_filter_used, vol_susp, vol_air_filt
                    - undo the vol_sus/(prop_filt * vol_air_filt) to get the INPS/filter
                    - subtract the blank from INPS/filter
                    - redo the vol_sus/(prop_filt * vol_air_filt) to get the INPS/L
                    Afterwards run check to see
                    if INP/L[-15] < INP/L[-14.5]: # if value decreases
                        # take previous value
                      INP/L[-15] = INP/L[-14.5]
                      # upper error is rmse of the one we throwing out and previous error
                      upper_INP/L[-15] = rtsmsqrs(upper error -15 and -14.5)
                      # lower CI is just the lower CI
                      lower_INP/L[-15] = lower INP/L[-14.5]
                    """

    def _extrapolate_blanks(self, missing_temps):
        """Extrapolate the blank correction for missing temperatures"""
        """
        What if you don't have blank data for the lowest extremes:
        Extrapolate out the blank using the slope of the previous 4 points
        Take error % of previous 4 points for error of the extrapolated points
        """
        blank_temps = []
        return blank_temps
