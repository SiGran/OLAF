from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.utils.df_utils import read_with_flexible_header, header_to_dict
from olaf.utils.path_utils import find_latest_file, is_within_dates
from olaf.utils.data_handler import DataHandler
from olaf.utils.plot_utils import filter_non_error_signal


class Plots:
    def __init__(self, project_folder: Path, includes, excludes, start_date, end_date) -> None:
        """

        Args:
            project_folder:
            includes:
            excludes:
            start_date:
            end_date:
        """
        self.project_folder = project_folder
        self.desired_files = self.find_desired_files(includes, excludes, start_date, end_date)

    #def plot_data(self):




    def find_desired_files(self, includes, excludes, start_date, end_date):
        """

        Args:
            includes:
            excludes:
            start_date:
            end_date:

        Returns:

        """
        start_date = datetime.strptime(start_date, "%m.%d.%y")
        end_date = datetime.strptime(end_date, "%m.%d.%y")

        file_paths = []
        for folder in self.project_folder.iterdir():
            if is_within_dates(dates=(start_date, end_date), folder_name=folder.name):
                if folder.is_dir() and not any(excl in folder.name for excl in excludes):
                    data_handler = DataHandler(
                        folder, 0, suffix=".csv", includes=includes, excludes=excludes, date_col=None
                    )
                    if data_handler.data_file and data_handler.data_file not in file_paths:
                        file_paths.append(data_handler.data_file)

        combined_df = pd.DataFrame()
        all_data = []

        for file in file_paths:
            header_lines, df = read_with_flexible_header(file)
            dict_header = header_to_dict(header_lines)

            df = df[df["INPS_L"] > 0]

            # Parse dates directly from the header dictionary
            if "start_time" in dict_header:
                date_str = dict_header["start_time"]
            else:
                print(f"start_time not found in {file.name}")

            # Find site from header dictionary
            if "site" in dict_header:
                site_str = dict_header["site"]
            else:
                print(f"site not found in {file.name}")

            if "treatment" in dict_header:
                treatment_str = dict_header["treatment"]
            else:
                print(f"treatment not found in {file.name}")

            site_date_str = site_str + " " + date_str
            df["site_date"] = site_date_str
            df["treatment"] = treatment_str

            all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data)
            else:
                raise ValueError("No valid data found in the provided files.")
        return combined_df








    #def _make_plot(self):