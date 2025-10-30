from math import ceil
from pathlib import Path

import pandas as pd

from olaf.utils.data_handler import DataHandler


class SpacedTempCSV(DataHandler):
    def __init__(
        self,
        folder_path: Path,
        num_samples,
        includes: tuple = ("base",),
        excludes: tuple = ("frozen",),
        date_col: str = "Date",
    ) -> None:
        """
        Class that has functionality to read a (processed ("verified")) well experiments
         .dat file from an experiment folder and process it into a .csv.
         This .csv contains temperature ranges with the number of frozen wells per sample.

        Args:
            folder_path: location of the experiment folder
            rev_name: list of strings to identify the revision name in the .dat file

        Returns:
            The data file and the data as a pandas DataFrame
        """
        includes = includes + ("reviewed",)
        super().__init__(
            folder_path, num_samples, includes=includes, excludes=excludes, date_col=date_col
        )
        return

    def create_temp_csv(
        self,
        dict_to_sample_dilution: dict,
        temp_step: float = 0.5,
        temp_col: str = "Avg_Temp",
        save: bool = True,
    ) -> pd.DataFrame:
        """
        Creates a .csv file that contains the number of frozen wells per sample at
        temperatures with intervals off "temp_steps" (default: 0.5 C).
        folder (...). This function is automatically ran after the last image is
        reviewed and the GUI closes. It uses the data file to find the first frozen well.
        The logic is as follows:
        1. find the first row with a non-zero value for least diluted sample.
        2. Round this value to 1 decimal (first_frozen)
        3. Floor this value to the nearest 0.5 (round_temp_frozen)
        4. subtract temp_step from that value (start_temp)
        5. Add (3) and (4) as first rows to df, add (2) in first loop of (7).
        6. Increment the temperature by temp_step until the end of the data.
        7. For each temperature, look at the band of temperatures that round to 1 decimal
           and find the (highest) number of frozen wells for each sample in that band.
        8. Save the data in a separate .csv file with the same name as the experiment.
        The data is saved in a separate .csv file with the same name as the experiment
        Args:
            temp_step: The interval of temperatures to save (default: 0.5)
            temp_col: The column in the data file that contains the temperature values
            save: Whether to save the data to a .csv file (default: True)
        Returns:
            Dataframe, and saves the data in a .csv file if save is True
        """
        # If using IS data look for "Avg_Temp" or if using cold plate data look for "Sample_Temp"
        if temp_col not in self.data.columns:
            alternative_col = "Sample_Temp" if temp_col == "Avg_Temp" else "Avg_Temp"
            if alternative_col in self.data.columns:
                temp_col = alternative_col
            else:
                raise KeyError(f"Neither '{temp_col}' nor '{alternative_col}' found in dataframe")

        # initialize the temp_frozen_df with temperature column and sample columns
        # step 1 and 2: Find least diluted sample from dict_to_sample_dilution
        least_diluted_sample = min(
            dict_to_sample_dilution, key=lambda k: dict_to_sample_dilution[k]
        )
        first_frozen_id = self.data[least_diluted_sample].ne(0).idxmax()
        temp_frozen = round(pd.to_numeric(self.data.loc[first_frozen_id, temp_col]), 1)
        # step 3: round down to nearest 0.5
        round_temp_frozen = ceil((temp_frozen * 2)) / 2
        # step 5: Initialize with three rows for the first two and zeros for the samples
        temp_first_frozen_row = [temp_frozen] + [
            self.data.loc[first_frozen_id, f"Sample_{i}"] for i in range(self.num_samples)
        ]
        temp_frozen_df = pd.DataFrame(
            data=[[round_temp_frozen + j * 0.5] + [0] * self.num_samples for j in range(4, 0, -1)],
            columns=[temp_col] + [f"Sample_{i}" for i in range(self.num_samples)],
        )
        temp_frozen_df.loc[len(temp_frozen_df)] = temp_first_frozen_row
        while round_temp_frozen - temp_step > min(self.data[temp_col]):
            # Step 6: increment the temperature by temp_step until the end of the data
            round_temp_frozen -= temp_step
            # Step 7: find the frozen wells for each temp
            round_temp_frozen_upper = round_temp_frozen + 0.01
            round_temp_frozen_lower = round_temp_frozen - 0.01
            # If no line is found within this range, it puts in NaN values. If there's
            # a NaN value, we want it to take the first temperature  below the range.

            new_row = [round_temp_frozen] + [
                self.data[
                    (self.data[temp_col] > round_temp_frozen_lower)
                    & (self.data[temp_col] < round_temp_frozen_upper)
                ][f"Sample_{i}"].max()
                if not pd.isna(
                    self.data[
                        (self.data[temp_col] > round_temp_frozen_lower)
                        & (self.data[temp_col] < round_temp_frozen_upper)
                    ][f"Sample_{i}"].max()
                )
                else self.data[self.data[temp_col] > round_temp_frozen_upper][f"Sample_{i}"].max()
                for i in range(self.num_samples)
            ]

            temp_frozen_df.loc[len(temp_frozen_df)] = new_row

        # Change temperature column to standard name of degC
        temp_frozen_df.rename(columns={temp_col: "degC"}, inplace=True)
        # Set sample columns to ints
        for i in range(self.num_samples):
            temp_frozen_df[f"Sample_{i}"] = temp_frozen_df[f"Sample_{i}"].astype("int64")
        # step 8
        if save:
            self.save_to_new_file(
                temp_frozen_df, self.folder_path / f"{self.data_file.stem}.csv", "frozen_at_temp"
            )

        return temp_frozen_df
