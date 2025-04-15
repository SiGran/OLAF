import numpy as np

from olaf.utils.df_utils import unique_dilutions


def inps_ml_to_L(inps_col, vol_air_filt, prop_filter_used, vol_susp):
    return (inps_col * vol_susp) / (vol_air_filt * prop_filter_used)


def inps_L_to_ml(inps_col, vol_air_filt, prop_filter_used, vol_susp):
    return (inps_col * vol_air_filt * prop_filter_used) / vol_susp


def rms(x):
    return np.sqrt(np.mean(np.square(x)))


def extrapolate_blanks(df_blanks, blank_temps, missing_temps):
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
                f"Warning: Non-monotonic behavior detected at temperature {df_blanks.index[i]}degC. "
                f"INP value decreases at colder temperature."
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

    return df_blanks, blank_temps
