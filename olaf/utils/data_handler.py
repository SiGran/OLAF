from pathlib import Path

import pandas as pd

from olaf.CONSTANTS import NUM_SAMPLES
from olaf.utils.path_utils import natural_sort_key


class DataHandler:
    def __init__(self, folder_path: Path, **kwargs) -> None:
        kwargs.setdefault("suffix", ".dat")
        kwargs.setdefault("includes", [""])
        kwargs.setdefault("excludes", None)
        kwargs.setdefault("date_col", "Time")
        kwargs.setdefault("sep", "\t")
        self.folder_path = folder_path

        self.data_file, self.data = self.get_data_file(
            suffix=kwargs["suffix"],
            includes=kwargs["includes"],
            excludes=kwargs["excludes"],
            date_col=kwargs["date_col"],
            sep=kwargs["sep"],
        )

    def get_data_file(
        self,
        includes: list[str],
        excludes: list[str],
        suffix: str = ".dat",
        date_col: str = "Time",
        sep: str = "\t",
    ) -> tuple[Path, pd.DataFrame]:
        """
        Load a file with a given suffix (default: .dat) from the Project folder.
        Arguments to exclude files can be passed as a list to the "excludes" parameter.
        Because of pandas loading, the Date and Time in column "Time" are split in two
        Different columns and renamed to Date and Time respectively.
        It also adds a column to capture changes to the number of frozen wells.
        The function returns the file path and the data as a pandas DataFrame.
        Args:
            suffix: suffix of the file to load (default: .dat)
            includes: combination of strings to include in the file name (default: None)
            excludes: combination of strings to exclude from the file name (default: None)
            date_col: column name for the date (or time) column (default: "Time")
            sep: separator for the file to load (default: tab-separated)
        Returns:
            tuple with the file path and the data as a pandas DataFrame
        """
        if excludes:
            files = [
                file
                for file in self.folder_path.iterdir()
                if file.suffix == suffix
                and all(name in file.name for name in includes)
                and not any(excl in file.name for excl in excludes)
            ]
        else:
            files = [
                file
                for file in self.folder_path.iterdir()
                if file.suffix == suffix and all(name in file.name for name in includes)
            ]
        if not files:
            raise FileNotFoundError("No files found with the given revision name")
        elif len(files) > 1:  # if more than one, pick the one with the highest counter
            data_file = sorted(files, key=lambda x: natural_sort_key(str(x)))[-1]
        else:  # if only one, pick that one
            data_file = files[0]

        data = pd.read_csv(data_file, sep=sep, parse_dates=[date_col])

        # If original .dat file, some changes are needed in this if statement
        if "Time" in data.columns and "Unnamed: 1" in data.columns and date_col == "Time":
            # rename automatically split datetime column
            data.rename(columns={"Time": "Date", "Unnamed: 1": "Time"}, inplace=True)
            # Add a column to capture changes to the number of frozen wells
            data["changes"] = [[0] * NUM_SAMPLES for _ in range(len(data))]
        if data.empty or data_file.name == "":
            raise FileNotFoundError("No .dat file found in the folder")

        return data_file, data

    def save_to_new_file(
        self,
        save_data: pd.DataFrame = None,
        save_path: Path = None,
        prefix: str = "reviewed",
        sep="\t",
    ) -> Path:
        """
                Save the data to a new file with the prefix "reviewed_" added to the name.
        Save a DataFrame to a new file with a unique name.
        Args:
            save_data: Pandas DataFrame to save
            save_path: pathlib.Path to save the file to (including directory)
            prefix: string to add to the start of the file name
            sep: separator for csv file to save too. Default is tab-separated

        Returns:
            pathlib.Path: Path to the saved file
        """
        if save_data is None:
            save_data = self.data
        if save_path is None:
            save_path = self.data_file.parent / self.data_file.name
        counter = 1
        # If the file already exists, add a number to the name
        save_path = save_path.parent / f"{prefix}_{save_path.name}"
        save_name_stem = save_path.stem  # get the stem of the file name to add number to
        while save_path.exists():
            save_path = save_path.parent / f"{save_name_stem}({counter}){save_path.suffix}"
            counter += 1
        save_data.to_csv(save_path, sep=sep, index=False)
        return save_path
