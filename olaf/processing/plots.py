from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

from olaf.utils.df_utils import read_with_flexible_header, header_to_dict
from olaf.utils.path_utils import find_latest_file, is_within_dates
from olaf.utils.data_handler import DataHandler
from olaf.utils.plot_utils import apply_plot_settings, PLOT_SETTINGS

# TODO: Add documentation for everything

class Plots:
    def __init__(self,
                 project_folder: Path,
                 includes,
                 excludes,
                 start_date,
                 end_date,
                 num_columns
                ) -> None:
        """

        Args:
            project_folder:
            includes:
            excludes:
            start_date:
            end_date:
        """
        self.project_folder = project_folder
        self.num_columns = num_columns
        self.desired_files_df = self.find_desired_files(includes, excludes, start_date, end_date)

    def plot_data(self, subplots = False, site_comparison = False):
        plots_folder = self.project_folder / "plots"
        if not plots_folder.exists():
            plots_folder.mkdir()
        save_path = plots_folder

        all_inp_data_df = self.desired_files_df.copy()

        unique_site_dates = all_inp_data_df["site_date"].unique() # note changed this come back
        # unique_site_dates = all_inp_data_df["date_time"].unique()
        # if site_comparison:
            # stuff

        n_dates = len(unique_site_dates)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        if subplots:
            # Create one figure with multiple subplots
            # need to make this a variable on main or a stop thing
            n_cols = min(self.num_columns, n_dates)
            n_rows = int(np.ceil(n_dates / n_cols))


            width_per_subplot = PLOT_SETTINGS['figure']['figsize'][0]
            height_per_subplot = PLOT_SETTINGS['figure']['figsize'][1]

            scale = PLOT_SETTINGS['figure']['subplot_scale']
            total_width = width_per_subplot * n_cols * scale
            total_height = height_per_subplot * n_rows * scale

            fig, axes = plt.subplots(n_rows, n_cols,
                                     figsize=(total_width, total_height),
                                     dpi=PLOT_SETTINGS['figure']['dpi'],
                                     squeeze=False)

            axes = axes.flatten()

            for idx, site_date in enumerate(unique_site_dates):
                ax = axes[idx]
                date_data = all_inp_data_df[all_inp_data_df["site_date"] == site_date]

                # Plot each treatment
                for treatment in date_data["treatment"].unique():
                    treatment_data = date_data[date_data["treatment"] == treatment]

                    # Calculate error bars (asymmetric)
                    yerr= [treatment_data["lower_CI"], treatment_data["upper_CI"]]
                    color = PLOT_SETTINGS['treatment_colors'].get(treatment, None)

                    ax.errorbar(treatment_data["degC"],
                                treatment_data["INPS_L"],
                                yerr=yerr,
                                label=treatment,
                                color = color,
                                **PLOT_SETTINGS['line'])

                ax.set_title(f'{site_date}')
                apply_plot_settings(ax, settings=PLOT_SETTINGS)

                # Hide extra subplots if any
            for idx in range(n_dates, len(axes)):
                axes[idx].set_visible(False)

            plt.tight_layout()

            plt.savefig(f'{save_path}/all_dates_combined_created_on-{current_time}.png', **PLOT_SETTINGS['save'])

        else:
            # Create separate figure for each date
            for site_date in unique_site_dates:
                fig, ax = plt.subplots(figsize=PLOT_SETTINGS['figure']['figsize'],
                                       dpi=PLOT_SETTINGS['figure']['dpi'])

                date_data = all_inp_data_df[all_inp_data_df["site_date"] == site_date]

                # Plot each treatment
                for treatment in date_data["treatment"].unique():
                    treatment_data = date_data[date_data["treatment"] == treatment]

                    # Calculate error bars (asymmetric)
                    yerr = [treatment_data["lower_CI"], treatment_data["upper_CI"]]
                    color = PLOT_SETTINGS['treatment_colors'].get(treatment, None)

                    ax.errorbar(treatment_data["degC"],
                                treatment_data["INPS_L"],
                                yerr=yerr,
                                label=treatment,
                                color = color,
                                **PLOT_SETTINGS['line'])

                ax.set_title(f'{site_date}')
                apply_plot_settings(ax, settings=PLOT_SETTINGS)
                plt.tight_layout()

                if save_path:
                    safe_date = str(site_date).replace('/', '_').replace(' ', '_').replace(':', '-')
                    plt.savefig(f'{save_path}/{safe_date}_created_on-{current_time}.png', **PLOT_SETTINGS['save'])



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

            ## TODO: Add site comparison code here
            """
            This should be something that says for date_str.unique, if site is not equal, don't combine 
            site and date? Or should I just not combine site_date_str at all and leave them as 
            separate columns in the combined_df. This might actually make things a lot more flexible?
            If they are all the same site, all you have to worry about is unique dates.
            One thing to think about in different locations is the timestamp being different.
            """

            site_date_str = site_str + " " + date_str
            df["site_date"] = site_date_str
            df["treatment"] = treatment_str

            # idea for just keeping these separate for the whole df to streamline
            # df["site"] = site_str
            # df["date_time"] = date_str
            # df["treatment"] = treatment_str

            all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data)
            else:
                raise ValueError("No valid data found in the provided files.")
        return combined_df

