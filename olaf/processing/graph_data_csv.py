import operator
from pathlib import Path

import numpy as np
import pandas as pd

from olaf.CONSTANTS import NUM_TO_REPLACE_D1, VOL_WELL, Z
from olaf.utils.data_handler import DataHandler


class GraphDataCSV(DataHandler):
    """
    This class is called after the last image is reviewed in the GUI closes,
    and after the .csv file with the temperature ranges and frozen wells is created.
    It has a function that reads in in above-mentioned .csv file and calculates the
    INPs/L to use per temperature over all the dilutions for the experiment.

    """

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
        includes: tuple = ("base",),
        excludes: tuple = ("INPs_L",),
        date_col=False,
    ) -> None:
        # Add class specific includes to make sure we get the right file
        includes = includes + ("frozen_at_temp", "reviewed")
        super().__init__(
            folder_path,
            num_samples,
            suffix=suffix,
            includes=includes,
            excludes=excludes,
            date_col=date_col,
            sep=",",
        )
        self.vol_air_filt = vol_air_filt
        self.wells_per_sample = wells_per_sample
        self.filter_used = filter_used
        self.vol_susp = vol_susp
        self.dict_to_samples_dilution = dict_samples_to_dilution
        # change the headers of the data from samples to dilution factor
        try:  # TODO REMOVE COLUMNS NOT IN DICT
            # Store original column names for verification
            original_columns = set(self.data.columns)

            # Drop columns that are not in dict_samples_to_dilution keys, except for 'degC'
            cols_to_keep = {"degC"}.union(dict_samples_to_dilution.keys())
            self.data = self.data[self.data.columns.intersection(list(cols_to_keep))]

            # Attempt to rename
            self.data.rename(columns=dict_samples_to_dilution, inplace=True)

            # Verify the renaming - modified to match the filtering logic
            expected_new_columns = {"degC"}.union(
                set(
                    value
                    for key, value in dict_samples_to_dilution.items()
                    if key in original_columns
                )
            )
            if set(self.data.columns) != expected_new_columns:
                raise ValueError("Column renaming did not produce expected results")

        except Exception as e:
            raise ValueError(f"Failed to rename columns: {str(e)}")
        return

    def convert_INPs_L(self, header: str, save=True):
        """
        Convert from # frozen wells at temperature for certain dilution to INPs/L.
        The steps involved in this function are:
        1. Seperate the temperature and # frozen well values.
        2. Create a column with the total number of wells per temperature
        as affected by the background.
        3. Calculate the INPs/L and the confidence intervals. It does this by using the
        number of wells frozen compared to the possible total number of wells.
        With the formula from <insert reference>:
        (INP/mL) = =(-LN((Dx-Ex)/Dx)/(Cx/1000))*Fx
        Dx = total number of wells minus the background
        Ex = number of frozen wells
        Cx = vol/well (microLiter)
        Fx = dilution factor
        4. Prune the data by removing the INF's and values that correspond with frozen wells
        This will allow for the logic in step 5 to function properly.
        5. Combine the data into one dataframe, using logic that makes decisions comparing
        the last 4 values of a dilution before it has more than 29/32 wells frozen.
        The logic for this is:
            <insert logic>
        6. Save and return the data.
        The result is a dataframe with the temperature, dilution factor, INPs/L, and the
        lower and upper confidence intervals.

        args:
            save: whether to save the data to a .csv file (default: True)

        Returns: the data as a pandas DataFrame

        """

        # Internal logic function for later use
        def error_logic_selecting_values(i, col_name, next_dilution_INP):
            """
            Logic for selecting the values to keep in the result_df when both current
            and next dilution are bigger than the previous temperature value.
            The logic is as follows:
            1. Check if the potential next temperature values are within the error range of
            the current temperature value
            2. If both are within the error range of the previous value, pick the one with
            the lowest (upper) error
            3. if only one is within the error range of the previous value, pick that one
            4. if both are outside of the error range, average them together

            Args:
                i: index of the df corresponding to a certain temperature
                col_name: col_name indicating the dilution factor
                next_dilution_INP: pandas series with the INPs/L for the next dilution
                specified with col_name

            Returns: none

            """
            curr_dilution = result_df.loc[i - 1, "dilution"]
            # upper CI of current one we're comparing so i-1
            current_upper_err = upper_INPS_p_L[curr_dilution][i - 1]
            # upper CI of possible next point with the same dilution
            next_upper_err = upper_INPS_p_L[curr_dilution][i]
            next_dil_upper_err = upper_INPS_p_L[col_name][i]
            # check if both/either one are within certain statistical range of
            # previous and next value
            if (result_df["INPS_L"][i - 1] + current_upper_err) > result_df["INPS_L"][i] and (
                result_df["INPS_L"][i - 1] + current_upper_err
            ) > next_dilution_INP[i]:
                # Both are within the error range of the previous value
                # Pick one with lowest error
                if next_upper_err < next_dil_upper_err:
                    return  # current one already selected
                else:
                    result_df.loc[i, "dilution"] = col_name
                    result_df.loc[i, "INPS_L"] = next_dilution_INP[i]
                    result_df.loc[i, "lower_CI"] = lower_INPS_p_L[col_name][i]
                    result_df.loc[i, "upper_CI"] = upper_INPS_p_L[col_name][i]
            # if one is within the error range of the previous value other isn't
            elif (result_df["INPS_L"][i - 1] + current_upper_err) > result_df["INPS_L"][i]:
                return  # current one already selected
            elif (result_df["INPS_L"][i - 1] + current_upper_err) > next_dilution_INP[i]:
                result_df.loc[i, "dilution"] = col_name
                result_df.loc[i, "INPS_L"] = next_dilution_INP[i]
                result_df.loc[i, "lower_CI"] = lower_INPS_p_L[col_name][i]
                result_df.loc[i, "upper_CI"] = upper_INPS_p_L[col_name][i]
            # both outside of error range
            else:
                # Average them together
                result_df.loc[i, "dilution"] = col_name
                result_df.loc[i, "INPS_L"] = (result_df.loc[i, "INPS_L"] + next_dilution_INP[i]) / 2
                # error propagation: sqrt(a^2 + b^2) / 2
                result_df.loc[i, "lower_CI"] = (
                    np.sqrt(result_df.loc[i, "lower_CI"] ** 2 + lower_INPS_p_L[col_name][i] ** 2)
                    / 2
                )
                result_df.loc[i, "upper_CI"] = (
                    np.sqrt(result_df.loc[i, "upper_CI"] ** 2 + upper_INPS_p_L[col_name][i] ** 2)
                    / 2
                )
            return

        "--------- Step 1: Separate temperature and # frozen well values -----------"

        # Take out temperature
        temps = self.data.pop("degC")
        # Sort the columns by dilution
        samples = self.data.reindex(sorted(self.data.columns), axis=1)

        "-------------- Step 2: Background column creation: N_total ---------------"
        most_diluted_value = max(
            v for v in self.dict_to_samples_dilution.values() if v != float("inf")
        )
        # check if any dilution is less than the background and take that instead
        # TODO: automatically false, only compare if background is above 2 frozen
        dilution_v_background_df = samples[float("inf")] > samples[most_diluted_value]
        # if more than NUM_TO_REPLACE_D1 samples in the highest dilutions are smaller
        # than the background
        # to create N_total df --> one column
        print(
            f"DI background found to be higher than {most_diluted_value} dilution "
            f"{dilution_v_background_df.sum()} times."
        )
        if dilution_v_background_df.sum() < NUM_TO_REPLACE_D1:
            N_total_series = self.wells_per_sample - samples[float("inf")]
            adjusted_samples = samples.apply(lambda col: col - samples[float("inf")])
        else:  # use the background
            N_total_series = self.wells_per_sample - samples[most_diluted_value]
            adjusted_samples = samples.apply(lambda col: col - samples[most_diluted_value])
            print(
                f"DI found to be higher than the {most_diluted_value} diltuion on "
                f"{dilution_v_background_df.sum()} occasions. "
                f"{most_diluted_value} dilution used for background in place of DI."
            )

        "--------------- Step 3: INP/L calc + Confidence Intervals ----------------------"
        # With the samples columns and the N_total column, we can calculate the INPs/L
        INPs_p_mL_test_water = adjusted_samples.apply(
            lambda col: (-np.log((N_total_series - col) / N_total_series) / (VOL_WELL / 1000))
            * float(col.name)
        )
        all_INPs_p_L = self._INP_ml_to_L(INPs_p_mL_test_water)
        lower_INPS_p_L, upper_INPS_p_L = self._error_calc(
            adjusted_samples, N_total_series, VOL_WELL, samples.columns
        )

        "-------------------------- Step 4: Pruning the data --------------------------"
        # Turn both positive and negative INF's into NaN's
        all_INPs_p_L.replace({np.inf: np.nan, -np.inf: np.nan}, inplace=True)
        # Turn the values that correspond with frozen wells (in samples) of 30 or higher into NaN's
        # TODO: this assumes all samples have 32 wells, which is not the case for lower temperatures
        # TODO: How to adjust for this?
        all_INPs_p_L[samples >= 30] = np.nan
        lower_INPS_p_L[samples >= 30] = np.nan
        upper_INPS_p_L[samples >= 30] = np.nan

        " -------------------------- Step 5: Combining into one -------------------------- "
        # initialize the results df with the first dilution
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

        # iterate over all consequent dilutions | skip the background | apply the logics
        for col_name, next_dilution_INP in all_INPs_p_L.iloc[:, 1:-1].items():
            # Take last 4 real values of current result_df["INPS_L"]
            last_4_i = result_df["INPS_L"].dropna().tail(4).index
            going_down = False
            for i in last_4_i:
                if (
                    result_df.loc[i, "INPS_L"] < result_df.loc[i - 1, "INPS_L"] or going_down
                ):  # If value is going down
                    going_down = True
                    prev_val = result_df["INPS_L"][i - 1]
                    if prev_val == np.nan:
                        prev_val = result_df["INPS_L"][i - 2]
                    if prev_val == np.nan:
                        print(
                            f"Dilution transition error going to dilution {col_name}; "
                            f"check frozen_at_temp file!"
                        )

                    # Check if both options are smaller
                    if result_df["INPS_L"][i] < prev_val and next_dilution_INP[i] < prev_val:
                        # throw them out/error, no value for that temperature, whatever
                        result_df.loc[i, :] = np.nan
                        # Both are bigger:
                    elif result_df["INPS_L"][i] > prev_val and next_dilution_INP[i] > prev_val:
                        # Logic moved to function at top of this function for readability
                        error_logic_selecting_values(i, col_name, next_dilution_INP)

                    # If only current dilution is bigger, take that one
                    elif result_df["INPS_L"][i] >= prev_val:
                        continue  # current one already selected
                    # If only next dilution is bigger, take that one
                    elif next_dilution_INP[i] >= prev_val:
                        result_df.loc[i, "dilution"] = col_name
                        result_df.loc[i, "INPS_L"] = next_dilution_INP[i]
                        result_df.loc[i, "lower_CI"] = lower_INPS_p_L[col_name][i]
                        result_df.loc[i, "upper_CI"] = upper_INPS_p_L[col_name][i]
                else:
                    continue
            # After checking the 4 overlapping values, we need to add the rest of the next dilution
            result_df.iloc[i + 1 :, 0] = col_name
            result_df.iloc[i + 1 :, 1] = next_dilution_INP[i + 1 :]
            result_df.iloc[i + 1 :, 2] = lower_INPS_p_L[col_name][i + 1 :]
            result_df.iloc[i + 1 :, 3] = upper_INPS_p_L[col_name][i + 1 :]
        # Add the temperature back as first column
        result_df.insert(0, "degC", temps)

        "---------------------- Step 6: Save and return the data ----------------------"
        if save:
            self.save_to_new_file(result_df, prefix="INPs_L", header=header)

        return result_df

    def _error_calc(self, n_frozen, n_total, vol_well: int | float, dilution, z: float = Z):
        """
        Calculate the error of the INP/L
        The formula used is in (2) from: Agresti, A., & Coull, B. A. (1998). Approximate is
        better than "exact" for interval estimation of binomial proportions.
        The American Statistician, 52(2), 119–126. https://doi.org/10.2307/2685469
        The formula is split up in three segments
        1. The plus/minus part to differentiate between the upper and lower confidence interval
        2. The remaining part of the numenator formula
        3. The denominator of the remaining part

        this calculates the values in INPs/mL and the typical conversion from mL to L
        applies for the errors too.
        Args:
            n_frozen: number of frozen wells measured; single value or pandas df
            n_total: total number of wells; single value or pandas series
            vol_well: volume of each well; single value
            dilution: dilution (-fold); single value or pandas series
            z: z-value of the normal distribution, float
        Returns:
            error of the INP/L
        """
        if isinstance(n_frozen, pd.DataFrame):  # dealing with a dataframes
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
            if isinstance(dilution, (int, float)):  # dealing with a single value
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
        """
        Convert the INPs/mL to INPs/L, using the formula::
        INPs/L = (INPs/mL * vol_susp) / (vol_air_filt * filter_used)
        with vol_susp = volume used for suspension
        vol_air_filt = volume of air filtered
        filter_used = proportion of filter used
        Args:
            ml_df: dataframe containing the INPs/mL values. Could also be a single
            value or series

        Returns: same format as input, but with INPs/L values

        """
        return (ml_df * self.vol_susp) / (self.vol_air_filt * self.filter_used)
