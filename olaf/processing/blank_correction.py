import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.CONSTANTS import DATE_PATTERN
from olaf.utils.df_utils import header_to_dict, read_with_flexible_header, unique_dilutions
from olaf.utils.math_utils import extrapolate_blanks, inps_L_to_ml, inps_ml_to_L, rms
from olaf.utils.path_utils import is_within_dates, natural_sort_key, save_df_file


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
        """Average all blank files into a single CSV file by temperature"""
        all_data = []

        # Track header information
        header_info = {}

        for file in self.blank_files:
            header_lines, df = read_with_flexible_header(file)
            dict_header = header_to_dict(header_lines)

            if not header_info:
                header_info.update(dict_header)
                header_info["start_time"] = datetime.strptime(
                    dict_header["start_time"], "%Y-%m-%d %H:%M:%S"
                )
                header_info["end_time"] = datetime.strptime(
                    dict_header["end_time"], "%Y-%m-%d %H:%M:%S"
                )

            # Parse dates directly from the header dictionary
            if "start_time" in dict_header:
                date_str = dict_header["start_time"]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

                if header_info["start_time"] > date_obj:
                    header_info["start_time"] = date_obj
            else:
                print(f"start_time not found in {file.name}")

            if "end_time" in dict_header:
                date_str = dict_header["end_time"]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

                if header_info["end_time"] < date_obj:
                    header_info["end_time"] = date_obj
            else:
                print(f"end_time not found in {file.name}")

            all_data.append(df)

        # Combine all blank dataframes
        combined_df = pd.concat(all_data)

        # Group by temperature bins and calculate average INPS/L and other stats
        grouped_INPS = (
            combined_df.groupby("degC")
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
            _, clean_df = self._save_combined_blanks(clean_df, header_info)

        self.combined_blank[(header_info["start_time"], header_info["end_time"])] = (
            clean_df,
            header_info,
        )
        return clean_df

    def _save_combined_blanks(self, clean_df, header_info):
        earliest = header_info["start_time"].strftime("%Y-%m-%d")
        latest = header_info["end_time"].strftime("%Y-%m-%d")
        # Save the combined blank data to a CSV file
        save_file = self.project_folder / f"combined_blank_{earliest}_{latest}.csv"
        # save_file, clean_df = save_df_file()
        counter = 0
        output_stem = save_file.stem
        while save_file.exists():
            # If the file exists, append a number to the filename
            counter += 1
            save_file = save_file.with_name(output_stem + f"({counter})" + save_file.suffix)

        with open(save_file, "w") as f:
            f.write(f"filename = {save_file.name}\n")
            for key, value in header_info.items():
                f.write(f"{key} = {value}\n")
            clean_df.to_csv(f, index=False)
        return save_file, clean_df

    def apply_blanks(self, save=True):
        """Apply the blank correction to all INPs/L files in the project folder"""

        for dates, data in self.combined_blank.items():
            df_blanks, header_info_blanks = data
            for experiment_folder in self.project_folder.iterdir():
                if "blank" not in experiment_folder.name and is_within_dates(
                    dates, experiment_folder.name
                ):
                    # Collect all INPs/L files in the experiment folder
                    input_files = list(experiment_folder.rglob("INPs_L*.csv"))
                    # pick the one with the highest number (latest)
                    input_files = sorted(input_files, key=lambda x: natural_sort_key(str(x)))

                    # Process the latest INPS file (assumes one relevant per folder)
                    # TODO: this can be done better
                    if len(input_files) > 2:
                        inps_file = input_files[-2]
                    else:
                        inps_file = input_files[-1]
                    header_lines, df_inps = read_with_flexible_header(inps_file)
                    dict_header = header_to_dict(header_lines)
                    # Check if the blank correction covers all temperatures from inps
                    inps_temps = df_inps["degC"]
                    blank_temps = df_blanks.index.to_series()
                    missing_temps = set(inps_temps) - set(blank_temps)
                    if missing_temps:
                        # If missing temp higher than highest blank temp, extrapolate
                        if max(missing_temps) > max(blank_temps):
                            # Extrapolate the blank correction
                            df_blanks, blank_temps = extrapolate_blanks(
                                df_blanks, blank_temps, missing_temps
                            )
                            missing_temps = set(inps_temps) - set(blank_temps)
                        if min(missing_temps) < min(blank_temps):
                            print(f"Missing temperatures in blank correction: {missing_temps}")

                    # Extract parameters
                    prop_filter_used = float(dict_header["proportion_filter_used"])
                    vol_susp = float(dict_header["vol_susp"])
                    vol_air_filt = float(dict_header["vol_air_filt"])
                    prop_filter_used_blanks = float(header_info_blanks["proportion_filter_used"])
                    vol_susp_blanks = float(header_info_blanks["vol_susp"])
                    vol_air_filt_blanks = float(header_info_blanks["vol_air_filt"])

                    # Set index to temperature for alignment
                    df_inps.set_index("degC", inplace=True)
                    # Create a new DataFrame for the corrected values
                    df_corrected = df_inps.copy()

                    # Convert to per filter units (vectorized)
                    df_inps["INPS_per_ml"] = inps_L_to_ml(
                        df_inps["INPS_L"], vol_air_filt, prop_filter_used, vol_susp
                    )

                    # Get blank values for matching temperatures
                    common_temps = df_inps.index.intersection(df_blanks.index)

                    # Vectorized operations for matching temperatures

                    blank_values = df_blanks.loc[common_temps, "INPS_L"]
                    blank_per_ml = inps_L_to_ml(
                        blank_values, vol_air_filt_blanks, prop_filter_used_blanks, vol_susp_blanks
                    )

                    # Subtract blanks (only for matching temperatures)
                    df_inps.loc[common_temps, "INPS_per_ml"] -= blank_per_ml

                    # Convert back to INPS/L (vectorized)
                    df_corrected["INPS_L"] = inps_ml_to_L(
                        df_inps["INPS_per_ml"], vol_air_filt, prop_filter_used, vol_susp
                    )

                    # Confidence interval correction (vectorized)
                    if "lower_CI" in df_inps.columns and "upper_CI" in df_blanks.columns:
                        # TODO add formula here with suspension, air_filtered, etc.
                        sample_lower = df_inps.loc[common_temps, "lower_CI"]
                        sample_lower = inps_L_to_ml(
                            sample_lower, vol_air_filt, prop_filter_used, vol_susp
                        )
                        sample_upper = df_inps.loc[common_temps, "upper_CI"]
                        sample_upper = inps_L_to_ml(
                            sample_upper, vol_air_filt, prop_filter_used, vol_susp
                        )
                        blank_lower = df_blanks.loc[common_temps, "lower_CI"]
                        blank_lower = inps_L_to_ml(
                            blank_lower,
                            vol_air_filt_blanks,
                            prop_filter_used_blanks,
                            vol_susp_blanks,
                        )
                        blank_upper = df_blanks.loc[common_temps, "upper_CI"]
                        blank_upper = inps_L_to_ml(
                            blank_upper,
                            vol_air_filt_blanks,
                            prop_filter_used_blanks,
                            vol_susp_blanks,
                        )

                        # Root sum of squares for error propagation
                        df_corrected.loc[common_temps, "lower_CI"] = inps_ml_to_L(
                            np.sqrt(sample_lower**2 + blank_lower**2),
                            vol_air_filt,
                            prop_filter_used,
                            vol_susp,
                        )
                        df_corrected.loc[common_temps, "upper_CI"] = inps_ml_to_L(
                            np.sqrt(sample_upper**2 + blank_upper**2),
                            vol_air_filt,
                            prop_filter_used,
                            vol_susp,
                        )

                    # Reset index to restore temperature column
                    df_corrected.reset_index(inplace=True)

                    # TODO: Final check
                    """
                    if INP/L[-15] < INP/L[-14.5]: # if value decreases
                        # take previous value
                      INP/L[-15] = INP/L[-14.5]
                      # upper error is rmse of the one we throwing out and previous error
                      upper_INP/L[-15] = rtsmsqrs(upper error -15 and -14.5)
                      # lower CI is just the lower CI
                      lower_INP/L[-15] = lower INP/L[-14.5]
                    """

                    # Save to output file
                    if save:
                        # Check if file has number in () at end and remove
                        if inps_file.stem.endswith(")"):
                            split_files = inps_file.stem.split("(")
                            if len(split_files) == 2:
                                save_file = (
                                    inps_file.parent
                                    / f"blank_corrected_{split_files[0]}{inps_file.suffix}"
                                )
                            else:
                                print(
                                    f"Difficulty saving corrected file name \n"
                                    f": {inps_file.stem} has more than one ()"
                                )

                        else:
                            save_file = inps_file.parent / f"blank_corrected_{inps_file.name}"
                        save_df_file(df_corrected, save_file, dict_header)
