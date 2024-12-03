import operator
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.CONSTANTS import NUM_TO_REPLACE_D1, VOL_WELL
from olaf.utils.data_handler import DataHandler


class GraphDataCSV(DataHandler):
    def __init__(
        self,
        folder_path: Path,
        num_samples,
        vol_air_filt: float,
        wells_per_sample: int,
        filter_used: float,
        vol_susp: float,
        dict_samples_to_dilution: dict,
        suffix: str = ".csv",
        includes: list[str] = None,
        date_col=False,
    ) -> None:
        if includes is None:
            includes = ["frozen_at_temp", "reviewed", "base"]
        super().__init__(
            folder_path, num_samples, suffix=suffix, includes=includes, date_col=date_col
        )
        self.vol_air_filt = vol_air_filt
        self.wells_per_sample = wells_per_sample
        self.filter_used = filter_used
        self.vol_susp = vol_susp
        # change the headers of the data from samples to dilution factor
        self.data.rename(columns=dict_samples_to_dilution, inplace=True)
        return

    def convert_INPs_L(self):
        """
        convert from frozen wells at temperature for certain dilution to INPs/L.
        1. Take frozen wells at temperature for certain dilution up to 29 wells,
        then go to next dilution.
        2. Calculate INPs/L with the formula:
        INPs/L =(Gx*$F$6)/($F$4*$F$5)
        with F4 = volume of air filtered
        F5 = proportion of filter used
        F6 = volume used for suspension

        With Gx being INP in test water (INP/mL) = =(-LN((Dx-Ex)/Dx)/(Cx/1000))*Fx
        Dx = total number of wells minus the background
        Ex = number of frozen wells
        Cx = vol/well (microLiter)
        Fx = dilution factor


        Returns:


        New plan after meeting 2024-10-28:
        1. Background correction first on the dataframe (take lowest dilution or DI)
        2. See Miro
        3. "" ""
        4. Take last four for next dilution
        5. It's accumulative, so if dilution drops, it's more likely a stochastic annomoly
        6. Profit

        if both options are smaller:
          throw them out/error, no value for that temperature, whtever
        elif both are bigger:
           check if both/either one are within certain statistical range of previous and next value
           if yes:
                take the one with least amount of error window
            if no:
                avg them together
        else:
            take the biggest one

        """
        # Take out temperature
        temps = self.data.pop("°C")
        # Sort the columns by dilution
        samples = self.data.reindex(sorted(self.data.columns), axis=1)

        # --------------- Step 2: Background column creation: N_total ------------------
        # check if any dilution is less than the background and take that instead
        dilution_v_background_df = samples[float("inf")] > samples[14641.0]
        # if more than NUM_TO_REPLACE_D1 samples in the highest dilutions are smaller
        # than the background
        # to create N_total df --> one column
        if dilution_v_background_df.sum() > NUM_TO_REPLACE_D1:
            N_total_series = self.wells_per_sample - samples[14641.0]
        else:  # use the background
            N_total_series = self.wells_per_sample - samples[float("inf")]
        # -------------------------- Step 3: INP/L calc --------------------------------
        """ With the samples columns and the N_total column, we can calculate the INPs/L"""
        INPs_p_mL_test_water = samples.apply(
            lambda col: (-np.log((N_total_series - col) / N_total_series) / (VOL_WELL / 1000))
            * float(col.name)
        )
        all_INPs_p_L = self._INP_ml_to_L(INPs_p_mL_test_water)
        lower_INPS_p_L, upper_INPS_p_L = self._error_calc(
            samples, N_total_series, VOL_WELL, samples.columns
        )
        # -------------------------- Step 4: Pruning the data --------------------------
        # Turn the INF's into NaN's
        all_INPs_p_L.replace(np.inf, np.nan, inplace=True)
        # Turn the values that correspond with frozen wells (in samples) of 30 or higher into NaN's
        all_INPs_p_L[samples >= 30] = np.nan
        lower_INPS_p_L[samples >= 30] = np.nan
        upper_INPS_p_L[samples >= 30] = np.nan
        # -------------------------- Step 5: Combining into one --------------------------

        # Combine the three Series into one DataFrame
        result_df = pd.concat(
            [
                pd.Series([all_INPs_p_L.columns[0]] * len(all_INPs_p_L)),
                all_INPs_p_L.iloc[:, 0],
                lower_INPS_p_L.iloc[:, 0],
                upper_INPS_p_L.iloc[:, 0],
            ],
            axis=1,
        )  # Rename the columns
        result_df.columns = ["dilution", "INPS_L", "lower_CI", "upper_CI"]
        for col_name, next_dilution_INP in all_INPs_p_L.iloc[:, 1:].items():
            # Take last 4 real values of current result_df["INPS_L"]
            last_4_i = result_df["INPS_L"].dropna().tail(4).index

            for i in last_4_i:
                # Check if both options are smaller
                if (
                    result_df["INPS_L"][i] < result_df["INPS_L"][i - 1]
                    and next_dilution_INP[i] < result_df["INPS_L"][i - 1]
                ):
                    # throw them out/error, no value for that temperature, whatever
                    result_df[i] = np.nan
                    # Both are bigger:
                elif (
                    result_df["INPS_L"][i] >= result_df["INPS_L"][i - 1]
                    and next_dilution_INP[i] >= result_df["INPS_L"].iloc[-1]
                ):
                    current_upper_err = upper_INPS_p_L[col_name][i - 1]
                    next_upper_err = upper_INPS_p_L[col_name][i]
                    next_dil_upper_err = upper_INPS_p_L[col_name][i]
                    # check if both/either one are within certain statistical range of
                    # previous and next value
                    if (result_df["INPS_L"][i - 1] + current_upper_err) > result_df["INPS_L"][
                        i
                    ] and (result_df["INPS_L"][i - 1] + current_upper_err) > next_dilution_INP[i]:
                        # Both are within the error range of the previous value
                        # Pick one with lowest error
                        if next_upper_err < next_dil_upper_err:
                            continue  # current one already selected
                        else:
                            result_df[i] = (
                                col_name,
                                next_dilution_INP[i],
                                lower_INPS_p_L[col_name][i],
                                upper_INPS_p_L[col_name][i],
                            )
                    # if one is within the error range of the previous value other isn't
                    elif (result_df["INPS_L"][i - 1] + current_upper_err) > result_df["INPS_L"][i]:
                        continue  # current one already selected
                    elif (result_df["INPS_L"][i - 1] + current_upper_err) > next_dilution_INP[i]:
                        result_df[i] = (
                            col_name,
                            next_dilution_INP[i],
                            lower_INPS_p_L[col_name][i],
                            upper_INPS_p_L[col_name][i],
                        )
                    # both outside of range
                    else:
                        # Average them together
                        result_df["dilution"][i] = col_name
                        result_df["INPS_L"][i] = (result_df["INPS_L"][i] + next_dilution_INP[i]) / 2
                        # error propagation: sqrt(a^2 + b^2) / 2
                        result_df["lower_CI"][i] = (
                            np.sqrt(
                                result_df["lower_CI"][i] ** 2 + lower_INPS_p_L[col_name][i] ** 2
                            )
                            / 2
                        )
                        result_df["upper_CI"][i] = (
                            np.sqrt(
                                result_df["upper_CI"][i] ** 2 + upper_INPS_p_L[col_name][i] ** 2
                            )
                            / 2
                        )

                # If only current dilution is bigger, take that one
                elif result_df["INPS_L"][i] >= result_df["INPS_L"][i - 1]:
                    continue  # current one already selected
                # If only next dilution is bigger, take that one
                elif next_dilution_INP[i] >= result_df["INPS_L"].iloc[-1]:
                    result_df[i] = (
                        col_name,
                        next_dilution_INP[i],
                        lower_INPS_p_L[col_name][i],
                        upper_INPS_p_L[col_name][i],
                    )

            # add the rest of the next dilution to the result_df
            result_df.iloc[i + 1 :, 0] = col_name
            result_df.iloc[i + 1 :, 1] = next_dilution_INP[i + 1 :]
            result_df.iloc[i + 1 :, 2] = lower_INPS_p_L[col_name][i + 1 :]
            result_df.iloc[i + 1 :, 3] = upper_INPS_p_L[col_name][i + 1 :]
        # Add the temperature back as first column
        result_df.insert(0, "°C", temps)
        return result_df

    def _error_calc(self, n_frozen, n_total, vol_well, dilution, z=1.96):
        """
        Calculate the error of the INP/L
        Args:
            z: z-value of the normal distribution
            no_frozen: number of frozen wells measured
            n_total: total number of wells
            vol_well: volume of each well
            dilution: dilution (-fold)
        Returns:
            error of the INP/L
        """
        if isinstance(n_frozen, pd.DataFrame):
            plus_min_part = n_frozen.apply(
                lambda col: z
                * np.sqrt((col / n_total * (1 - col / n_total) + z**2 / (4 * n_total)) / n_total)
            )
            rem_num = n_frozen.apply(lambda col: (col / n_total) + z**2 / (2 * n_total))
            denom = 1 + z**2 / n_total
        else:  # We're dealing with a single value
            plus_min_part = z * np.sqrt(
                (n_frozen / n_total * (1 - n_frozen / n_total) + z**2 / (4 * n_total)) / n_total
            )
            rem_num = (n_frozen / n_total) + z**2 / (2 * n_total)
            denom = 1 + z**2 / n_total
        conf_intervals = []
        for op in [operator.sub, operator.add]:
            if isinstance(dilution, int or float):
                limit_wells = (op(rem_num, plus_min_part) / denom) * n_total
                limit_INPS_ml = (
                    dilution / (vol_well / 1000) * (n_frozen - limit_wells) / (n_total - n_frozen)
                )
            else:  # We're dealing with matrices/dfs so dilution is the column names
                limit_wells = rem_num.apply(
                    lambda col: (op(col, plus_min_part[col.name]) / denom) * n_total
                )
                limit_INPS_ml = limit_wells.apply(
                    lambda col: col.name
                    / (vol_well / 1000)
                    * abs((n_frozen[col.name] - col))
                    / (n_total - n_frozen[col.name])
                )
            limit_INPS_L = self._INP_ml_to_L(limit_INPS_ml)
            conf_intervals.append(limit_INPS_L)

        return conf_intervals

    def _INP_ml_to_L(self, ml_df):
        return (ml_df * self.vol_susp) / (self.vol_air_filt * self.filter_used)
