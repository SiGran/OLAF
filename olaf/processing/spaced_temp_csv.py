from math import ceil
from pathlib import Path

import pandas as pd

from olaf.CONSTANTS import NUM_SAMPLES
from olaf.utils.path_utils import natural_sort_key, save_to_new_file


class SpacedTempCSV:
    def __init__(self, folder_path: Path, rev_name: list[str] = None):
        """
        Class that has functionality to read a (processed ("verified")) well experiments
         .dat file from a experiment folder and process it into a .csv.
         This .csv contains temperature ranges with
        ex
        Args:
            folder_path: Loc
            rev_name:
        """
        self.folder_path = folder_path
        if rev_name is None:
            rev_name = ["reviewed"]
        self.data_file, self.data = self._read_dat_file(rev_name)
        return

    def _read_dat_file(self, rev_name):
        # Find all the .dat files with the given revision name in the file name
        files = [
            file
            for file in self.folder_path.iterdir()
            if file.suffix == ".dat" and all(name in file.name for name in rev_name)
        ]
        if not files:
            raise FileNotFoundError("No files found with the given revision name")
        elif len(files) > 1:  # if more than one, pick the one with the highest counter
            data_file = natural_sort_key(files)[-1]
        else:  # if only one, pick that one
            data_file = files[0]
        data = pd.read_csv(data_file, sep="\t", parse_dates=["Date"])
        return data_file, data

    def create_temp_csv(
        self, temp_step: float = 0.5, temp_col: str = "Avg_Temp", save: bool = True
    ) -> pd.DataFrame:
        """
        Creates a .csv file that contains the number of frozen wells per sample at
        temperatures with intervals off "temp_steps" (default: 0.5 C).
        folder (...). This function is automatically ran after the last image is
        reviewed and the GUI closes. It uses the data file to find the first frozen well.
        The logic is as follows:
        1. find the first row with a non-zero value for any sample.
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
            Dataframe, and saves the data in a .csv file
            :param save:
        """
        # initialize the temp_frozen_df with temperature column and sample columns
        # step 1 and 2: find first frozen row
        first_frozen_id_col = [self.data[f"Sample_{i}"].ne(0).idxmax() for i in range(NUM_SAMPLES)]
        first_frozen_id = min(first_frozen_id_col)
        temp_frozen = round(self.data.loc[first_frozen_id, temp_col], 1)
        # step 3: round down to nearest 0.5
        round_temp_frozen = ceil((temp_frozen * 2)) / 2
        # step 5: Initialize with three rows for the first two and zeros for the samples
        temp_first_frozen_row = [temp_frozen] + [
            self.data.loc[first_frozen_id, f"Sample_{i}"] for i in range(NUM_SAMPLES)
        ]
        temp_frozen_df = pd.DataFrame(
            data=[[round_temp_frozen + j * 0.5] + [0] * NUM_SAMPLES for j in range(4, 0, -1)],
            columns=[temp_col] + [f"Sample_{i}" for i in range(NUM_SAMPLES)],
        )
        temp_frozen_df.loc[len(temp_frozen_df)] = temp_first_frozen_row
        while round_temp_frozen - temp_step > min(self.data[temp_col]):
            # Step 6: increment the temperature by temp_step until the end of the data
            round_temp_frozen -= temp_step
            # Step 7: find the frozen wells for each temp
            round_temp_frozen_upper = round_temp_frozen + 0.01
            round_temp_frozen_lower = round_temp_frozen - 0.01
            new_row = [round_temp_frozen] + [
                self.data[
                    (self.data[temp_col] > round_temp_frozen_lower)
                    & (self.data[temp_col] < round_temp_frozen_upper)
                ][f"Sample_{i}"].max()
                for i in range(NUM_SAMPLES)
            ]
            temp_frozen_df.loc[len(temp_frozen_df)] = new_row

        # Change temperature column to standard name of °C
        temp_frozen_df.rename(columns={temp_col: "°C"}, inplace=True)
        # Set sample columns to ints
        for i in range(NUM_SAMPLES):
            temp_frozen_df[f"Sample_{i}"] = temp_frozen_df[f"Sample_{i}"].astype("int64")
        # step 8
        if save:
            save_to_new_file(
                temp_frozen_df, self.folder_path / f"{self.data_file.stem}.csv", "frozen_at_temp"
            )

        return temp_frozen_df
