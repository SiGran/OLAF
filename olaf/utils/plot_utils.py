import matplotlib.pyplot as plt


def plot_INPS_L(result_df):
    """
    Plots the INP concentrations from the result DataFrame.

    Parameters:
    - result_df: DataFrame containing the INP data with columns 'Temperature (degC)',
      'n_INP_STP (per L)', 'lower_CL (per L)', 'upper_CL (per L)', and 'Treatment_flag'.

    Returns:
    - None: Displays the plot.
    """

    # Plotting the INP concentrations
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        result_df["Temperature (degC)"],
        result_df["n_INP_STP (per L)"],
        yerr=[result_df["lower_CL (per L)"], result_df["upper_CL (per L)"]],
        fmt="o",
        label="INP Concentration",
        capsize=5,
    )

    plt.title("Ice Nucleating Particles Concentration")
    plt.xlabel("Temperature (degC)")
    plt.ylabel("INP Concentration (per L)")
    plt.grid()
    plt.legend()
    plt.show()
