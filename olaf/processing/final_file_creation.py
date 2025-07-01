import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from olaf.CONSTANTS import DATE_PATTERN, ERROR_SIGNAL
from olaf.utils.data_handler import DataHandler
from olaf.utils.df_utils import header_to_dict, read_with_flexible_header


class FinalFileCreation:
    def __init__(self, project_folder: Path, includes, excludes) -> None:
        """ """
        self.project_folder = project_folder
        self.files_per_date = self._get_files_per_date(includes, excludes)

    def _get_files_per_date(self, includes, excludes):
        """
        Get all the files in the project folder and group them by date.
        """
        file_paths = []
        # Go through every folder in the project folder and create a data_handler object for it
        for folder in self.project_folder.iterdir():
            if folder.is_dir() and not any(excl in folder.name for excl in excludes):
                data_handler = DataHandler(
                    folder, 0, suffix=".csv", includes=includes, excludes=excludes, date_col=None
                )
                if data_handler.data_file and data_handler.data_file not in file_paths:
                    file_paths.append(data_handler.data_file)

        files_per_date = {}
        for file in file_paths:
            # look for the "start_time" in the header
            header_lines, _ = read_with_flexible_header(file)
            dict_header = header_to_dict(header_lines)
            found_dates = dict_header["start_time"]
            if not found_dates:
                print(f"No date found in file name: {file.name}")
                continue
            else:
                # Check if the date is already in the dictionary
                if found_dates not in files_per_date:
                    files_per_date[found_dates] = []
                files_per_date[found_dates].append(file)

        return files_per_date

    def create_all_final_files(self, treatment_dict, header_start) -> None:
        """
        Create a final file with all the data from the files in the project folder.
        """
        # Create a folder for the final files
        final_file_folder = self.project_folder / "final_files"
        if not final_file_folder.exists():
            final_file_folder.mkdir()

        # Iterate through all the files per date in the project folder
        for date, files in self.files_per_date.items():
            header = header_start
            save_file = None  # placeholder for file saving name
            notes = ""  # string to fill out with the notes from all the files

            dfs_to_concat = []  # List to hold dataframes for concatenation

            # Go through each file and add it to the final df
            for file in files:
                # Read the file and get the header data
                header_lines, df_inps = read_with_flexible_header(file)
                dict_header = header_to_dict(header_lines)
                notes += f"{dict_header['notes']}. "
                if save_file is None:  # on First read, set save_file and extend header
                    save_file = final_file_folder / (
                        f"{dict_header['site']}"
                        f"{dict_header['start_time'][0:10]}_"
                        f"{dict_header['start_time'][11:].replace(':', '')}.csv"
                    )

                    header += f"Site: {dict_header['site']}\n"
                    header += f"Filter color: {dict_header['filter_color']}\n"

                # Get the treatment flag from the file name
                treatment_flag = ERROR_SIGNAL
                for treatment, flag in treatment_dict.items():
                    if treatment in file.name:
                        treatment_flag = flag
                        break
                if treatment_flag == ERROR_SIGNAL:
                    print(f"Treatment flag not found in file name: {file.name}")
                    continue

                temp_df = df_inps.drop("dilution", axis=1)
                temp_df["Treatment_flag"] = treatment_flag
                temp_df["lower_CI"] = df_inps["INPS_L"] - df_inps["lower_CI"]
                temp_df["upper_CI"] = df_inps["INPS_L"] + df_inps["upper_CI"]

                temp_df.rename(
                    columns={
                        "degC": "Temperature (degC)",
                        "INPS_L": "n_INP_STP (per L)",
                        "lower_CI": "lower_CL (per L)",
                        "upper_CI": "upper_CL (per L)",
                    },
                    inplace=True,
                )
                # Final check before concatenating
                temp_df = self._final_check(temp_df)

                # Add the dataframe to the list for concatenation
                dfs_to_concat.append(temp_df)

            # Concatenate all dataframes in the list
            if dfs_to_concat:
                final_df = pd.concat(dfs_to_concat, ignore_index=True)
            else:
                final_df = pd.DataFrame(
                    columns=[
                        "Temperature (degC)",
                        "n_INP_STP (per L)",
                        "lower_CL (per L)",
                        "upper_CL (per L)",
                        "Treatment_flag",
                    ]
                )

            # Add all the notes to the header
            header += f"Sample notes: {notes}\n"
            # Add the columns manually
            header += (
                "Start (UTC)\t Stop (UTC)\t Total_vol (L)\n"
                "Temperature (degC)\t n_INP_STP (per L)\t lower_CL (per L)\t "
                "upper_CL (per L)\t Treatment_flag\n"
            )
            # Convert both start_time and end_time to UTC seconds
            start_dt_obj = datetime.strptime(dict_header["start_time"], "%Y-%m-%d %H:%M:%S")
            end_dt_obj = datetime.strptime(dict_header["end_time"], "%Y-%m-%d %H:%M:%S")

            # Convert to UTC timestamp (seconds since epoch)
            start_utc_seconds = int(start_dt_obj.timestamp())
            end_utc_seconds = int(end_dt_obj.timestamp())

            # Replace the old line with the new timestamps
            header += f"{start_utc_seconds}\t {end_utc_seconds}\t {dict_header['vol_air_filt']}\n"
            if save_file is not None:
                with open(save_file, "w", newline="") as f:
                    f.write(header)
                    final_df.to_csv(f, sep=",", index=False, header=False)
            else:
                print(f"Warning: No save file created for date {date} in {self.project_folder}")

    def _final_check(self, df):
        """
        Final check for the dataframe. If lower_CI (TOTAL VALUE) is below 0, set it to
        error signal.
        """

        # NOTE: completely redundant when removing all zero values
        # in the blank_correction _final_check() function
        # Remove all the rows at the start where n_INP_STP (per L) is 0
        # Find where n_INP_STP is not zero
        non_zero_mask = abs(df["n_INP_STP (per L)"]) > 1e-10

        if non_zero_mask.any():
            # Get index of first non-zero value
            first_non_zero_idx = non_zero_mask.idxmax()
            # Keep only rows starting from the first non-zero value
            df = df.iloc[first_non_zero_idx:]

        # If any lower_CL (per L) is below 0, then set all that go below to error signal
        if df["lower_CL (per L)"].min() < 0:
            df.loc[df["lower_CL (per L)"] < 0, "lower_CL (per L)"] = ERROR_SIGNAL
        return df
