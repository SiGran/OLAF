from pathlib import Path
import pandas as pd


from olaf.utils.data_handler import DataHandler
"""
Not sure yet it if this should be a function or a class. What we want to do:
There will be a folder within the parent folder of the sample folder that contains a DI run
    ie path = Path.cwd().parent / cold plate runs 10.30.25 / 10.30.25 di
This is how the day will be started before doing any cold plate runs
Within that folder there will be a frozen_at_temp_reviewed file.

Now, when we have a sample
    ie path = Path.cwd().parent / cold plate runs 10.30.25 / Mosaic 06.02.20 base
    
we want this cold_plate_di function/class to do a couple of things:
    1. Read in the frozen_at_temp_reviewed file for Mosaic 06.02.20 base
    2. Read in the frozen_at_temp_reviewed file for 10.30.25 di
    3. Append sample_0 data from the di frozen_at_temp_reviewed file to the Mosaic file
    4. Return the updated Mosaic file and save it
"""

class ColdPlateDi(DataHandler):
    def __init__(
            self,
            folder_path: Path,
            num_samples,
            suffix: str = ".csv",
            includes: tuple = ("base",),
            excludes: tuple = ("INPs_L",),
            date_col=False,
    ) -> None:
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

    def append_di_to_sample_reviewed_file(
        self,
        dict_samples_to_dilution: dict,
        save: bool = True,
        ) -> pd.DataFrame:

        # Look in the dictionary where the user has designated they want the DI column to be
        for key, value in dict_samples_to_dilution.items():
            if value == float("inf"):
                desired_di_column = key
                break

        # Look for di frozen_at_temp_reviewed files from this day
        potential_di_files = []
        for experiment_day_folder in self.folder_path.parent.iterdir():
            if experiment_day_folder.is_dir() and ("di" in experiment_day_folder.name.lower()):
                for file_path in experiment_day_folder.rglob("frozen_at_temp_reviewed*csv"):
                    potential_di_files.append(file_path)

        # Read all DI files, group them into one df and average each
        # temperature bin's frozen droplet values
        di_dfs = [pd.read_csv(file) for file in potential_di_files]
        if di_dfs:
            combined_di_df = pd.concat(di_dfs)
        else:
            raise ValueError("No valid DI data found in the provided files.")
        grouped_di_df = combined_di_df.groupby("degC").agg({"Sample_0": "mean"})

        # Replace designated DI column in sample data with the di data
        sample_reviewed_df = self.data # sample data file
        sample_reviewed_df[desired_di_column] = (sample_reviewed_df["degC"]
                                          .map(grouped_di_df["Sample_0"])
                                          .round(decimals=1))
        # If the first freezer from the sample is not in the di column,
        # fill nan with previous temp bin di value
        sample_reviewed_df[desired_di_column] = sample_reviewed_df[desired_di_column].ffill()

        if save:
            self.save_to_new_file(
                sample_reviewed_df, self.folder_path / f"{self.data_file.stem}.csv", "_di_appended"
            )

