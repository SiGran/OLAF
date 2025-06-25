import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from olaf.CONSTANTS import THRESHOLD_ERROR


def plot_INPS_L(result_df, save_path, header_dict):
    """
    Plots the INP concentrations from the result DataFrame.

    Parameters:
    - result_df: DataFrame containing the INP data with columns 'Temperature (degC)',
      'n_INP_STP (per L)', 'lower_CL (per L)', 'upper_CL (per L)', and 'Treatment_flag'.

    Returns:
    - None: Displays the plot.
    """
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)

    # Plotting the INP concentrations
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        result_df["degC"][4:],
        result_df["INPS_L"][4:],
        yerr=[result_df["lower_CI"][4:], result_df["upper_CI"][4:]],
        fmt="o",
        label="INP Concentration",
        capsize=2,
        color="darkblue",
    )
    site = header_dict["site"]
    plt.title(
        f"Ice Nucleating Particles Number Concentration at {site} for "
        f"{header_dict['start_time'][:10]}"
    )
    plt.xlabel("Temperature (degC)")
    plt.ylabel("INP Concentration (per L STP)")
    plt.yscale("log")
    plt.ylim(
        result_df[result_df["lower_CI"] > 0]["lower_CI"].min() * 0.1, result_df["INPS_L"].max() * 3
    )
    plt.xlim(-30, 0)
    plt.xticks(np.arange(0, -35, -5))
    plt.gca().set_xticks(np.arange(0, -31, -1), minor=True)
    plt.grid(True, linestyle="--", color="gray", linewidth=0.5)
    plt.grid(True, which="major", alpha=0.5)  # Major grid lines
    plt.grid(True, which="minor", alpha=0.1)
    if "TBS" in site:
        legend_elements = [
            Patch(facecolor="none", edgecolor="none", label=f"Site: {site}"),
            Patch(
                facecolor="none", edgecolor="none", label=f"Date: {header_dict['start_time'][:10]}"
            ),
            Patch(
                facecolor="none", edgecolor="none", label=f"Treatment: {header_dict['treatment']}"
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Lower altitude: {header_dict['lower_altitude']} m agl",
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Upper altitude: {header_dict['upper_altitude']} m agl",
            ),
        ]
    else:
        legend_elements = [
            Patch(facecolor="none", edgecolor="none", label=f"Site: {site}"),
            Patch(
                facecolor="none", edgecolor="none", label=f"Date: {header_dict['start_time'][:10]}"
            ),
            Patch(
                facecolor="none", edgecolor="none", label=f"Treatment: {header_dict['treatment']}"
            ),
        ]
    plt.legend(
        handles=legend_elements, markerscale=0, handlelength=0, handletextpad=0, loc="upper right"
    )
    plt.savefig(save_path)
    # plt.show()


def plot_blank_corrected_vs_pre_corrected_inps(
    df_corrected, df_original, save_path, plot_header_info
):
    """
    Creates individual plots for each sample being blank corrected.
    Plots show the pre-corrected INP spectrum
    and the post-corrected INP spectrum.
    Parameters
    ----------
    df_corrected
    df_original
    plot_header_info
    save_path

    Returns
    -------
    plot_blank_corrected_vs_pre_corrected_INPs
    """
    # Add pre-corrected data to the plot
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        df_original["degC"][4:],
        df_original["INPS_L"][4:],
        label="Pre-corrected INP Concentration",
        yerr=[df_original["lower_CI"][4:], df_original["upper_CI"][4:]],
        fmt="o",
        capsize=2,
        color="lightsteelblue",
    )
    # Check for -9999 in corrected data and remove before plotting
    plot_eligible_data = filter_non_error_signal(df_corrected)
    # Add blank corrected data to the plot
    plt.errorbar(
        plot_eligible_data["degC"],
        plot_eligible_data["INPS_L"],
        label="Blank corrected INP Concentration",
        yerr=[plot_eligible_data["lower_CI"], plot_eligible_data["upper_CI"]],
        fmt="o",
        capsize=2,
        color="darkred",
    )
    # Plot formatting
    site = plot_header_info["site"]
    plt.title(
        f"Ice Nucleating Particles Number Concentration at {site} for "
        f"{plot_header_info['start_time'][:10]}"
    )
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.xlabel("Temperature (degC)")
    plt.ylabel("INP Concentration (per L STP)")
    plt.yscale("log")
    plt.ylim(
        df_corrected[df_corrected["lower_CI"] > 0]["lower_CI"].min() * 0.1,
        df_corrected["INPS_L"].max() * 3,
    )
    plt.xlim(-30, 0)
    plt.xticks(np.arange(0, -35, -5))
    plt.gca().set_xticks(np.arange(0, -31, -1), minor=True)
    plt.grid(True, linestyle="--", color="gray", linewidth=0.5)
    plt.grid(True, which="major", alpha=0.5)  # Major grid lines
    plt.grid(True, which="minor", alpha=0.1)
    if "TBS" in site:
        legend_elements = [
            Patch(facecolor="none", edgecolor="none", label=f"Site: {site}"),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Date: {plot_header_info['start_time'][:10]}",
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Treatment: {plot_header_info['treatment']}",
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Lower altitude (m agl): {plot_header_info['lower_altitude']}",
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Upper altitude (m agl): {plot_header_info['upper_altitude']}",
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Total volume collected (L STP): {plot_header_info['vol_air_filt']}",
            ),
            Patch(
                facecolor="none", edgecolor="none", label=f"Error Threshold: {THRESHOLD_ERROR} %"
            ),
        ]
    else:
        legend_elements = [
            Patch(facecolor="none", edgecolor="none", label=f"Site: {site}"),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Date: {plot_header_info['start_time'][:10]}",
            ),
            Patch(
                facecolor="none",
                edgecolor="none",
                label=f"Treatment: {plot_header_info['treatment']}",
            ),
            Patch(
                facecolor="none", edgecolor="none", label=f"Error Threshold: {THRESHOLD_ERROR} %"
            ),
        ]
    all_handles = handles + legend_elements
    plt.legend(
        handles=all_handles, markerscale=0, handlelength=0, handletextpad=1, loc="upper right"
    )
    plt.savefig(save_path)


def filter_non_error_signal(df_corrected):
    """
    Removes error signal values from df_corrected to avoid plotting errors due to negative
    values in a log.
    Parameters
    ----------
    df_corrected

    Returns
    -------
    filtered_df_corrected
    """
    error_signal_mask = df_corrected["INPS_L"] < 0
    plot_eligible_data = df_corrected[~error_signal_mask]
    return plot_eligible_data
