from pathlib import Path
from typing import Any

import pandas as pd

from olaf.utils.path_utils import find_latest_file


class DataHandler:
    def __init__(self, folder_path: Path, num_samples: int, **kwargs) -> None:
        kwargs.setdefault("suffix", ".dat")
        kwargs.setdefault("includes", ())
        kwargs.setdefault("excludes", ())
        kwargs.setdefault("date_col", "Time")
        kwargs.setdefault("sep", "\t")

        self.folder_path = folder_path
        self.num_samples = num_samples
        self.data_file, self.data = self.get_data_file(
            suffix=kwargs["suffix"],
            includes=kwargs["includes"],
            excludes=kwargs["excludes"],
            date_col=kwargs["date_col"],
            sep=kwargs["sep"],
        )

        return

    def get_data_file(
        self,
        includes: tuple,
        excludes: tuple,
        suffix: str = ".dat",
        date_col: str = "Time",
        sep: str = "\t",
    ) -> tuple[Any, Any]:
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
        if excludes or includes:
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
            return (
                None,
                FileNotFoundError(
                    f"No files found in {self.folder_path} with "
                    f"suffix {suffix} that includes {includes} and "
                    f"excludes {excludes}"
                ),
            )
        elif len(files) > 1:  # if more than one, pick the one with the highest counter
            data_file = find_latest_file(files)
        else:  # if only one, pick that one
            data_file = files[0]

        if date_col:
            data = pd.read_csv(data_file, sep=sep, parse_dates=[date_col])
        else:
            data = pd.read_csv(data_file, sep=sep)
        # If original .dat file, some changes are needed in this if statement
        if "Time" in data.columns and "Unnamed: 1" in data.columns and date_col == "Time":
            # rename automatically split datetime column
            data.rename(columns={"Time": "Date", "Unnamed: 1": "Time"}, inplace=True)
            # Add a column to capture changes to the number of frozen wells
            data["changes"] = [[0] * self.num_samples for _ in range(len(data))]
        if data.empty or data_file.name == "":
            raise FileNotFoundError("No .dat file found in the folder")

        return data_file, data

    def save_to_new_file(
        self,
        save_data: pd.DataFrame | None = None,
        save_path: Path | None = None,
        prefix: str = "_",
        sep: str = ",",
        header: str | None = None,
    ) -> Path:
        """
        Save a DataFrame to a new file with a unique name.

        If the target file already exists, automatically adds a number suffix
        to create a unique filename.

        Args:
            save_data: Pandas DataFrame to save. If None, uses self.data
            save_path: Path to save the file to. If None, uses self.data_file
            prefix: String to add to the start of the file name
            sep: Separator for CSV file (default: comma)
            header: Header to add to the file. If None, no header is added
        Returns:
            Path: Path to the saved file

        Raises:
            ValueError: If save_data is None and self.data is not available
            TypeError: If save_path is not a Path object
            OSError: If there are file system related errors
        """
        # Validate inputs
        if save_data is None:
            if not hasattr(self, "data"):
                raise ValueError("No data provided and self.data not available")
            save_data = self.data

        if save_path is None:
            if not hasattr(self, "data_file"):
                raise ValueError("No save_path provided and self.data_file not available")
            save_path = self.data_file

        if not isinstance(save_path, Path):
            raise TypeError("save_path must be a Path object")

        # Create the initial save path with prefix
        save_path = save_path.parent / f"{prefix}_{save_path.name}"
        save_name_stem = save_path.stem  # Get the stem of the file before numbers are added to it

        # Find a unique filename
        counter = 1
        while save_path.exists():
            save_path = save_path.parent / f"{save_name_stem}({counter}){save_path.suffix}"
            counter += 1

        try:
            # Ensure the parent directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the data
            with open(save_path, "w") as f:
                if header:
                    if isinstance(header, dict):
                        for key, value in header.items():
                            f.write(f"{key} = {value}\n")
                    else:
                        f.write(f"{header}\n")
                save_data.to_csv(f, sep=sep, index=False, lineterminator="\n")
            return save_path

        except OSError as e:
            raise OSError(f"Error saving file to {save_path}: {str(e)}")
