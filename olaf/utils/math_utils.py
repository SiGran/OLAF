"""Mathematical utility functions for INP calculations and conversions."""

import numpy as np


def inps_ml_to_L(inps_col, vol_air_filt, prop_filter_used, vol_susp):
    """Convert Ice Nucleating Particles per milliliter to per Liter of air at STP.

    This conversion accounts for the air sample volume, the proportion of the filter
    used in the experiment, and the suspension volume.

    Args:
        inps_col: Ice Nucleating Particles per milliliter (INPs/mL).
        vol_air_filt: Volume of air filtered through the sample (L).
        prop_filter_used: Proportion of the filter used (0.0 to 1.0).
        vol_susp: Volume of suspension (mL).

    Returns:
        Ice Nucleating Particles per Liter of air at STP (INPs/L).

    Example:
        >>> inps_ml_to_L(inps_col=10.0, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0)
        0.161
    """
    return (inps_col * vol_susp) / (vol_air_filt * prop_filter_used)


def inps_L_to_ml(inps_col, vol_air_filt, prop_filter_used, vol_susp):
    """Convert Ice Nucleating Particles per Liter of air to per milliliter of suspension.

    This is the inverse conversion of inps_ml_to_L, converting from atmospheric
    concentration back to suspension concentration.

    Args:
        inps_col: Ice Nucleating Particles per Liter of air at STP (INPs/L).
        vol_air_filt: Volume of air filtered through the sample (L).
        prop_filter_used: Proportion of the filter used (0.0 to 1.0).
        vol_susp: Volume of suspension (mL).

    Returns:
        Ice Nucleating Particles per milliliter of suspension (INPs/mL).

    Example:
        >>> inps_L_to_ml(inps_col=0.161, vol_air_filt=620.48, prop_filter_used=1.0, vol_susp=10.0)
        10.0
    """
    return (inps_col * vol_air_filt * prop_filter_used) / vol_susp


def rms(x):
    """Calculate the Root Mean Square (RMS) of an array.

    The RMS is calculated as the square root of the arithmetic mean of the
    squares of the values.

    Args:
        x: Array-like input values.

    Returns:
        Root mean square of the input values as a scalar.

    Example:
        >>> rms([1, 2, 3, 4, 5])
        3.316...
    """
    return np.sqrt(np.mean(np.square(x)))
