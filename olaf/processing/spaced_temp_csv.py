from math import ceil
from pathlib import Path

import pandas as pd

from olaf.CONSTANTS import (
    INITIAL_ROWS_FOR_TEMP,
    TEMP_ROUNDING_INTERVAL,
    TEMP_TOLERANCE,
)
from olaf.utils.data_handler import DataHandler


class SpacedTempCSV(DataHandler):
    """Creates temperature-binned CSV files from Ice Nucleation Spectrometer data.

    This class processes reviewed/verified .dat files from freezing experiments and
    converts them into CSV files with temperature-stepped data. Each temperature
    step (default 0.5°C) shows how many wells were frozen at that temperature
    for each sample. This binning is necessary for calculating INP concentrations
    as a function of temperature.

    Inherits from DataHandler for file loading and data management.

    Attributes:
        Inherits all attributes from DataHandler parent class.
    """

    def __init__(
        self,
        folder_path: Path,
        num_samples,
        includes: tuple = ("base",),
        excludes: tuple = ("frozen",),
        date_col: str = "Date",
    ) -> None:
        """Initialize the SpacedTempCSV processor.

        Args:
            folder_path: Path to the experiment folder containing data files.
            num_samples: Number of samples in the experiment.
            includes: Tuple of strings that must be in filename (default: ("base",)).
            excludes: Tuple of strings to exclude from filename (default: ("frozen",)).
            date_col: Name of the date column in the data (default: "Date").
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
        # initialize the temp_frozen_df with temperature column and sample columns
        # step 1 and 2: Find least diluted sample from dict_to_sample_dilution
        least_diluted_sample = min(
            dict_to_sample_dilution, key=lambda k: dict_to_sample_dilution[k]
        )
        first_frozen_id = self.data[least_diluted_sample].ne(0).idxmax()
        temp_frozen = round(pd.to_numeric(self.data.loc[first_frozen_id, temp_col]), 1)
        # step 3: round down to nearest temperature interval
        round_temp_frozen = ceil((temp_frozen / TEMP_ROUNDING_INTERVAL)) * TEMP_ROUNDING_INTERVAL
        # step 5: Initialize with initial rows for the first temperatures and zeros for the samples
        temp_first_frozen_row = [temp_frozen] + [
            self.data.loc[first_frozen_id, f"Sample_{i}"] for i in range(self.num_samples)
        ]
        temp_frozen_df = pd.DataFrame(
            data=[
                [round_temp_frozen + j * TEMP_ROUNDING_INTERVAL] + [0] * self.num_samples
                for j in range(INITIAL_ROWS_FOR_TEMP, 0, -1)
            ],
            columns=[temp_col] + [f"Sample_{i}" for i in range(self.num_samples)],
        )
        temp_frozen_df.loc[len(temp_frozen_df)] = temp_first_frozen_row
        while round_temp_frozen - temp_step > min(self.data[temp_col]):
            # Step 6: increment the temperature by temp_step until the end of the data
            round_temp_frozen -= temp_step
            # Step 7: find the frozen wells for each temp
            round_temp_frozen_upper = round_temp_frozen + TEMP_TOLERANCE
            round_temp_frozen_lower = round_temp_frozen - TEMP_TOLERANCE
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
