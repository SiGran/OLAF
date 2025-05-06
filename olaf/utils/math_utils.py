import numpy as np


def inps_ml_to_L(inps_col, vol_air_filt, prop_filter_used, vol_susp):
    return (inps_col * vol_susp) / (vol_air_filt * prop_filter_used)


def inps_L_to_ml(inps_col, vol_air_filt, prop_filter_used, vol_susp):
    return (inps_col * vol_air_filt * prop_filter_used) / vol_susp


def rms(x):
    return np.sqrt(np.mean(np.square(x)))
