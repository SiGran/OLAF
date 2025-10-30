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
        save: bool = True,
        ) -> pd.DataFrame:

        # Look for di frozen_at_temp_reviewed files from this day
        potential_di_files = []
        for experiment_day_folder in self.folder_path.parent.iterdir():
            if experiment_day_folder.is_dir() and ("di" in experiment_day_folder.name.lower()):
                for file_path in experiment_day_folder.rglob("frozen_at_temp_reviewed*csv"):
                    potential_di_files.append(file_path)

        # Read all DI files
        di_dfs = [pd.read_csv(file) for file in potential_di_files]
        if len(potential_di_files) > 1:
            # Use first file as base (keeps temperature column)
            df_di_avg = di_dfs[0].copy()

            # Get second column name
            # TODO: breaks down here, need to figure out why
            freezing_data_col = df_di_avg.columns["Sample_0"]

            # Average the second column values from all dataframes
            df_di_avg[freezing_data_col] = sum(df[freezing_data_col] for df in di_dfs) / len(di_dfs)
            print(f"Averaged {len(potential_di_files)} DI files (column: {freezing_data_col})")
        else:
            df_di_avg = di_dfs[0]

        appended_frozen_df = self.data.copy # this is the sample file
        appended_frozen_df["Sample_5"] = df_di_avg["Sample_0"]

        if save:
            self.save_to_new_file(
                appended_frozen_df, self.folder_path / f"{self.data_file.stem}.csv", "frozen_at_temp_di_appended"
            )

