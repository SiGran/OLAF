from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.utils.df_utils import read_with_flexible_header, header_to_dict
from olaf.utils.path_utils import find_latest_file

class Analyze:
    def __init__(self, project_folder: Path, treatment_plot = False,
                 comparison_plot = False, timeline_plot = False) -> None:
        self.project_folder = project_folder
        self.desired_files = self.find_desired_files(
            treatment_plot=treatment_plot,
            comparison_plot=comparison_plot,
            timeline_plot=timeline_plot
        )

    def find_desired_files(self, treatment_plot = False, comparison_plot = False, timeline_plot=False):
        if treatment_plot or timeline_plot:
            base_files = []
            heat_files = []
            peroxide_files = []

            # Single iteration through directories
            for experiment_folder in self.project_folder.iterdir():
                if not experiment_folder.is_dir():
                    continue

                folder_name_lower = experiment_folder.name.lower()
                matching_files = list(experiment_folder.rglob("INPs_L*.csv"))
                most_recent_files = find_latest_file(matching_files)

                if "base" in folder_name_lower:
                    base_files.append(most_recent_files)
                elif "heat" in folder_name_lower:
                    heat_files.append(most_recent_files)
                elif "peroxide" in folder_name_lower:
                    peroxide_files.append(most_recent_files)

            return base_files, heat_files, peroxide_files
        if comparison_plot:
            comparison_files = []
            for experiment_folder in self.project_folder.iterdir():
                if not experiment_folder.is_dir():
                    continue

                matching_files = list(experiment_folder.rglob("INPs_L*.csv"))
                comparison_files.extend(matching_files)
            return comparison_files
        return None
    
    def plot_treatment_data(self, base_files, heat_files, peroxide_files, treatment_plot=True):
        if treatment_plot:
            for file in base_files:
                self.read_inp_data(file)
            for file in heat_files:
                self.read_inp_data(file)
            for file in peroxide_files:
                self.read_inp_data(file)


    def read_inp_data(self, files):
        for file in files:
            header_lines, df = read_with_flexible_header(file)
            dict_header = header_to_dict(header_lines)

            # Filter out zero and negative INPS values
            df = df[df["INPS_L"] > 0]

            # Track header information
            header_info = {}

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
