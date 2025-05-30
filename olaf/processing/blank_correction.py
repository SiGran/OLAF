from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.CONSTANTS import ERROR_SIGNAL, THRESHOLD_ERROR
from olaf.utils.df_utils import header_to_dict, read_with_flexible_header, unique_dilutions
from olaf.utils.math_utils import inps_L_to_ml, inps_ml_to_L, rms
from olaf.utils.path_utils import (
    find_latest_file,
    is_within_dates,
    save_df_file,
    sort_files_by_date,
)


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
            if experiment_folder.is_dir() and "blank" in experiment_folder.name.lower():
                for file_path in experiment_folder.rglob("INPs_L*.csv"):
                    potential_blank_files.append(file_path)

        # Group the files by date
        files_by_date = sort_files_by_date(potential_blank_files)

        # Select the file with the highest trailing number for each date
        blank_files = []
        for date, files in files_by_date.items():
            # Sort by the number (second element of tuple) in descending order
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

            # Filter out zero and negative INPS values
            df = df[df["INPS_L"] > 0]

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
            clean_df.to_csv(f, index=True, lineterminator="\n")
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
                    # Process the latest INPS file (assumes one relevant per folder)
                    # Select the appropriate INPs/L file for processing
                    if not input_files:
                        raise FileNotFoundError(f"No INPs_L files found in {experiment_folder}")

                    # Filter out any previously blank-corrected files
                    original_files = [f for f in input_files if "blank_corrected" not in f.name]

                    if not original_files:
                        raise FileNotFoundError(
                            f"Only blank-corrected files found in {experiment_folder}"
                        )

                    # Get the latest original file (highest numbered or most recent)
                    inps_file = find_latest_file(original_files)
                    print(f"Selected {inps_file.name} for blank correction")

                    header_lines, df_inps = read_with_flexible_header(inps_file)
                    dict_header = header_to_dict(header_lines)
                    # Check if the blank correction covers all temperatures from inps

                    # Store the original dataframe before filtering
                    df_original = df_inps.copy()

                    # Find zero INPS rows to be preserved in the final output
                    zero_rows_mask = df_inps["INPS_L"] == 0
                    df_zero_rows = df_inps[zero_rows_mask].copy()

                    # Remove rows with zero INPS values for blank correction
                    df_inps = df_inps[~zero_rows_mask]

                    # Continue with the blank correction process using the filtered dataframe
                    inps_temps = df_inps["degC"]
                    blank_temps = df_blanks.index.to_series()
                    missing_temps = set(inps_temps) - set(blank_temps)
                    if missing_temps:
                        # If missing temp higher than highest blank temp, extrapolate
                        if max(missing_temps) > max(blank_temps):
                            # Extrapolate the blank correction
                            df_blanks, blank_temps = self._extrapolate_blanks(
                                df_blanks, blank_temps, missing_temps, dates
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

                    # Before concatenating, ensure the index is set to temperature
                    df_zero_rows.set_index("degC", inplace=True)
                    if not df_zero_rows.empty:
                        # Reinsert zero INPS rows
                        df_corrected = pd.concat([df_zero_rows, df_corrected], axis=0)

                    # Reset index to restore temperature column and sort
                    df_corrected = df_corrected.sort_index(ascending=False)
                    df_corrected.reset_index(inplace=True)
                    df_corrected = self._final_check(df_corrected, df_original)

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
                        save_df_file(df_corrected, save_file, dict_header, index=False)

    def _final_check(self, df_corrected, df_inps):
        """
        Add info with how many times corrected value is below lower CI
        Check for monotonicity - INP/L should not decrease with decreasing temperature
        """
        # Check how many times corrected values go below the lower CI of originals
        corrected_below_ci = []
        for temp in df_corrected.index:
            # Check if the corrected value is below the lower CI of the original
            if (
                df_corrected.loc[temp, "INPS_L"]
                < df_inps.loc[temp, "INPS_L"] - df_inps.loc[temp, "lower_CI"]
            ):
                # If so, store the temperature
                corrected_below_ci.append(temp)

        if (len(corrected_below_ci) / len(df_corrected)) * 100 > THRESHOLD_ERROR:
            # Replace all the temperatures, and CI's with error value
            for temp in corrected_below_ci:
                print(
                    f"value {df_corrected.loc[temp, 'INPS_L']} for temperature {temp} "
                    f"outside temperature range, replacing with error value {ERROR_SIGNAL}"
                )
                df_corrected.loc[temp, "INPS_L"] = ERROR_SIGNAL
        else:
            # Get sorted temperatures for monotonic check
            indices = sorted(df_corrected.index)  # Higher to lower temp

            # Loop through temperatures, starting from the second one
            for i in range(1, len(indices)):
                current_temp = indices[i]
                prev_temp = indices[i - 1]

                # Check if INP/L decreases with lower temperature (non-monotonic)
                if df_corrected.loc[current_temp, "INPS_L"] < df_corrected.loc[prev_temp, "INPS_L"]:
                    # TODO: edge case handling for when current or previous is ERROR_SIGNAL!
                    print(f"Correcting value at temperature {current_temp}")
                    # Take previous value
                    df_corrected.loc[current_temp, "INPS_L"] = df_corrected.loc[prev_temp, "INPS_L"]
                    # Upper error is rmse of the one we throwing out and previous error
                    df_corrected.loc[current_temp, "upper_CI"] = rms(
                        [
                            df_corrected.loc[current_temp, "upper_CI"],
                            df_corrected.loc[prev_temp, "upper_CI"],
                        ]
                    )
                    # Lower CI is just the lower CI
                    df_corrected.loc[current_temp, "lower_CI"] = df_corrected.loc[
                        prev_temp, "lower_CI"
                    ]

        return df_corrected

    def _extrapolate_blanks(self, df_blanks, blank_temps, missing_temps, dates, save=True):
        """Extrapolate the blank correction for missing temperatures"""
        """
        What if you don't have blank data for the lowest extremes:
        Extrapolate out the blank using the slope of the previous 4 points
        Take error % of previous 4 points for error of the extrapolated points
        """
        # Find missing temperatures that are below the current minimum
        min_blank_temp = min(blank_temps)
        extrapolation_temps = [temp for temp in missing_temps if temp < min_blank_temp]

        if not extrapolation_temps:
            print(f"No extrapolation occured for missing temperatures: {missing_temps}")
            return df_blanks, blank_temps

        # Check if the last (or any other value) is lower than previous ones
        # We expect INP values to increase as temperature decreases
        if len(df_blanks) > 1 and df_blanks["INPS_L"].iloc[-1] < df_blanks["INPS_L"].iloc[-2]:
            print(
                f"Warning: Last temperature {df_blanks.index[-1]}degC has lower INP value "
                f"than previous temperature. Excluding from slope calculation."
            )

            # Use the 4 points before the last one
            if len(df_blanks) >= 5:
                last_four = df_blanks.iloc[-5:-1]
            else:
                last_four = df_blanks.iloc[:-1]

            # Add the excluded temperature to extrapolation list
            if df_blanks.index[-1] not in extrapolation_temps:
                extrapolation_temps.append(df_blanks.index[-1])
        else:
            # No issues with monotonicity at the end, use the last 4 points
            last_four = df_blanks.tail(4)

        # Check for other non-monotonic behavior in the dataset
        for i in range(1, len(df_blanks) - 1):
            if df_blanks["INPS_L"].iloc[i] > df_blanks["INPS_L"].iloc[i + 1]:
                print(
                    f"Warning: Non-monotonic behavior detected at temperature "
                    f"{df_blanks.index[i]}degC. INP value decreases at colder temperature."
                )

        # Calculate the slope using linear regression on these points
        x = last_four.index.to_numpy()  # Temperatures
        y = last_four["INPS_L"].to_numpy()  # INPS_L values

        # Simple linear regression: calculate slope
        fit = np.polyfit(x, y, 1)

        # Calculate average error percentages for last 4 points
        # Avoid division by zero (with the 0.001)
        error_percents = {
            "lower_CI": (last_four["lower_CI"] / np.maximum(last_four["INPS_L"], 0.001)).mean(),
            "upper_CI": (last_four["upper_CI"] / np.maximum(last_four["INPS_L"], 0.001)).mean(),
        }

        # Use all the unique dilutions from the points used for extrapolation
        dilution = unique_dilutions(last_four["dilution"])

        for temp in sorted(extrapolation_temps, reverse=True):
            # Calculate extrapolated INPS_L using the slope
            extrapolated_inps = fit[1] + fit[0] * temp

            # Calculate CIs based on average error percentages
            lower_ci = extrapolated_inps * error_percents["lower_CI"]
            upper_ci = extrapolated_inps * error_percents["upper_CI"]

            # Add the new row to df_blanks
            df_blanks.loc[temp] = {
                "dilution": dilution,
                "INPS_L": extrapolated_inps,
                "lower_CI": lower_ci,
                "upper_CI": upper_ci,
                "blank_count": 0,  # Mark as extrapolated
            }

        # Sort again to ensure proper order
        df_blanks = df_blanks.sort_index(ascending=False)

        # Calculate new blanks temps
        blank_temps = df_blanks.index.to_series()

        # Save the new blank here?
        if save:
            # Save the updated DataFrame to a CSV file
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_file = (
                self.project_folder
                / f"extrap_comb_b_correction_range_{dates[0].strftime('%Y%m%d_%H%M%S')}_"
                f"{dates[1].strftime('%Y%m%d_%H%M%S')}_created_on-{current_time}.csv"
            )
            print(f"Saving extrapolated blanks to {save_file}")
            df_blanks.to_csv(save_file, index=True)
        return df_blanks, blank_temps
