from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

from olaf.utils.df_utils import read_with_flexible_header, header_to_dict
from olaf.utils.path_utils import find_latest_file, is_within_dates
from olaf.utils.data_handler import DataHandler
from olaf.utils.plot_utils import apply_plot_settings, PLOT_SETTINGS


class Plots:
    def __init__(self,
                 project_folder: Path,
                 includes: tuple,
                 excludes: tuple,
                 start_date: str,
                 end_date: str,
                 num_columns: int,
                 site_markers: dict,
                 save_name: str
                ) -> None:
        """
        This class is used for plotting INP spectra and can make lots of individual plots
        with or without site comparisons, or a single figure of subplots with or without
        site comparisons. Future additions may include timeline plots using plotly for
        publication or poster ready figures.
        TODO: "site" might be best changed to "identifier" so the user can use whatever
        TODO: organizer they want. Would need to be a variable accessible to all functions.
        Args:
            project_folder: Path variable
            includes: tuple, generally "INPS_L" and other strings
            excludes: tuple, generally "blank" and other strings
            start_date: User defined starting date from which to pull data. mm.dd.yy format
            end_date: User defined date from which to pull data. mm.dd.yy format
            num_columns: Integer set by user if creating subplots
            site_markers: Dictionary of site markers
            save_name: String of user desired save name if creating subplots
        """
        self.project_folder = project_folder
        self.num_columns = num_columns
        self.site_markers = site_markers
        self.save_name = save_name
        self.desired_files_df = self.find_desired_files(includes, excludes, start_date, end_date)


    def plot_data(self, subplots = False, site_comparison = False, tbs = False):
        """
        Function with multiple options for plotting INP data.
        Args:
            subplots: bool
            site_comparison: bool

        Returns: None, saves image(s)

        """
        # Create folder to store images within project folder
        plots_folder = self.project_folder / "plots"
        if not plots_folder.exists():
            plots_folder.mkdir()
        save_path = plots_folder

        all_inp_data_df = self.desired_files_df.copy()

        # Remove timestamps in case they are slightly different for site comparisons
        if site_comparison:
            date_version = "date_time"
            if tbs:
                all_inp_data_df[date_version] = all_inp_data_df[date_version].astype(str).str[0:10]
            else:
                all_inp_data_df[date_version] = all_inp_data_df[date_version].astype(str).str[0:10]
        else:
            date_version = "site_date"

        # Obtain unique dates or site dates depending on plot
        unique_site_dates = all_inp_data_df[date_version].unique()

        # for sizing and saving
        n_dates = len(unique_site_dates)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        if subplots:
            n_cols = min(self.num_columns, n_dates) #user chooses num_columns on main_plots
            n_rows = int(np.ceil(n_dates / n_cols))

            # sizing of subplots
            width_per_subplot = PLOT_SETTINGS['figure']['figsize'][0]
            height_per_subplot = PLOT_SETTINGS['figure']['figsize'][1]

            # sizing of figure
            scale = PLOT_SETTINGS['figure']['subplot_scale']
            total_width = width_per_subplot * n_cols * scale
            total_height = height_per_subplot * n_rows * scale

            # make figure
            fig, axes = plt.subplots(n_rows, n_cols,
                                     figsize=(total_width, total_height),
                                     dpi=PLOT_SETTINGS['figure']['dpi'],
                                     squeeze=False)
            # flatten to 1D array
            axes = axes.flatten()

            for idx, date in enumerate(unique_site_dates):
                ax = axes[idx]

                date_data = all_inp_data_df[all_inp_data_df[date_version] == date]

                sites = date_data["site"].unique()

                for site in sites:
                    if site_comparison:
                        site_data = date_data[date_data["site"] == site]
                    else: site_data = date_data

                    marker = self.site_markers.get(site) # not sure if the 'o' is needed

                # Plot each treatment
                    for treatment in site_data["treatment"].unique():
                        treatment_data = site_data[site_data["treatment"] == treatment]

                        # Calculate error bars (asymmetric)
                        yerr= [treatment_data["lower_CI"], treatment_data["upper_CI"]]
                        color = PLOT_SETTINGS['treatment_colors'].get(treatment, None)

                        if site_comparison and site != 'default':
                            label = f"{site} - {treatment}"
                        else:
                            label = treatment

                        if tbs:
                            lower_alt = treatment_data["lower_altitude"].iloc[0]
                            upper_alt = treatment_data["upper_altitude"].iloc[0]
                            label = label + f" {lower_alt}m - {upper_alt}m"
                        else:
                            label = label

                        # Manually add marker setting
                        line_settings = PLOT_SETTINGS['line'].copy()
                        line_settings['marker'] = marker

                        ax.errorbar(treatment_data["degC"],
                                    treatment_data["INPS_L"],
                                    yerr=yerr,
                                    label=label,
                                    color = color,
                                    **line_settings)

                        ax.set_title(f'{date}')
                    apply_plot_settings(ax, settings=PLOT_SETTINGS)

                # Hide extra subplots if any
            for idx in range(n_dates, len(axes)):
                axes[idx].set_visible(False)

            plt.tight_layout()

            plt.savefig(f'{save_path}/{self.save_name}_created_on-{current_time}.png', **PLOT_SETTINGS['save'])

        else:
            # Create separate figure for each date
            for date in unique_site_dates:
                fig, ax = plt.subplots(figsize=PLOT_SETTINGS['figure']['figsize'],
                                       dpi=PLOT_SETTINGS['figure']['dpi'])

                date_data = all_inp_data_df[all_inp_data_df[date_version] == date]

                sites = date_data["site"].unique()

                for site in sites:
                    if site_comparison:
                        site_data = date_data[date_data["site"] == site]
                    else:
                        site_data = date_data

                    marker = self.site_markers.get(site)

                    # Plot each treatment
                    for treatment in site_data["treatment"].unique():
                        treatment_data = site_data[site_data["treatment"] == treatment]

                        # Calculate error bars (asymmetric)
                        yerr = [treatment_data["lower_CI"], treatment_data["upper_CI"]]
                        color = PLOT_SETTINGS['treatment_colors'].get(treatment, None)

                        if site_comparison and site != 'default':
                            label = f"{site} - {treatment}"
                        else:
                            label = treatment

                        if tbs:
                            lower_alt = treatment_data["lower_altitude"].iloc[0]
                            upper_alt = treatment_data["upper_altitude"].iloc[0]
                            label = label + f" {lower_alt}m - {upper_alt}m"
                        else:
                            label = label

                        line_settings = PLOT_SETTINGS['line'].copy()
                        line_settings['marker'] = marker

                        ax.errorbar(treatment_data["degC"],
                                    treatment_data["INPS_L"],
                                    yerr=yerr,
                                    label=label,
                                    color = color,
                                    **line_settings)

                    if site_comparison:
                        ax.set_title(f'{date}')
                    else:
                        ax.set_title(f'{site} {date}')
                    apply_plot_settings(ax, settings=PLOT_SETTINGS)
                plt.tight_layout()

                if site_comparison or tbs:
                    save_site = site + "_"
                else:
                    save_site = ""

                if save_path:
                    safe_date = str(date).replace('/', '_').replace(' ', '_').replace(':', '-')
                    plt.savefig(f'{save_path}/{save_site}{safe_date}_created_on-{current_time}.png', **PLOT_SETTINGS['save'])



    def find_desired_files(self, includes, excludes, start_date, end_date):
        """

        Args:
            includes: User defined on main. INPS_L is primary, can specify specific treatments,
            blank corrected, sites, etc.
            excludes: User defined on main. Blanks excluded, can be customized like includes.
            start_date: In mm.dd.yy format
            end_date: In mm.dd.yy format

        Returns: combined_df. Df with columns of degC, INPS_L, lower_CI, upper_CI,
        site_date, site, date_time and treatment. Site_date is the site and full date_time
        strings combined.

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
            # probably a cleaner way to do this
            if "blank_corrected" in includes:
                header_lines, df = read_with_flexible_header(file, expected_columns=("degC", "dilution", "INPS_L", "lower_CI", "upper_CI", "qc_flag"))
            else:
                header_lines, df = read_with_flexible_header(file)
            dict_header = header_to_dict(header_lines)

            # Remove zero or ERROR_SIGNAL (if below zero)
            df = df[df["INPS_L"] > 0]

            # Parse dates directly from the header dictionary
            if "start_time" in dict_header:
                date_str = dict_header["start_time"]
            else:
                print(f"start_time not found in {file.name}")

            # Find site and treatment from header dictionary
            if "site" in dict_header:
                site_str = dict_header["site"]
            else:
                print(f"site not found in {file.name}")

            if "treatment" in dict_header:
                treatment_str = dict_header["treatment"]
            else:
                print(f"treatment not found in {file.name}")

            # Creating df columns for easier access by the plot_data function
            # Can add more from dict_header if desired
            site_date_str = site_str + " " + date_str
            df["site_date"] = site_date_str
            df["site"] = site_str
            df["date_time"] = date_str
            df["treatment"] = treatment_str

            if "TBS" in site_str:
                df["lower_altitude"] = dict_header["lower_altitude"]
                df["upper_altitude"] = dict_header["upper_altitude"]


            all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data)
            else:
                raise ValueError("No valid data found in the provided files.")
        return combined_df

