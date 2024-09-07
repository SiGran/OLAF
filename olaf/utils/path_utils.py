import re
from pathlib import Path

import pandas as pd


def natural_sort_key(s):
    """
    Key function for sorting strings in "natural" order.
    Args:
        s:

    Returns:

    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def save_to_new_file(save_data: pd.DataFrame, save_name: Path, prefix: str = "", sep="\t") -> Path:
    """
    Save a DataFrame to a new file with a unique name.
    Args:
        save_data: Pandas DataFrame to save
        save_name: pathlib.Path to save the file to
        prefix: string to add to the start of the file name
        sep: separator for csv file to save too. Default is tab-separated

    Returns:
        pathlib.Path: Path to the saved file
    """
    counter = 1
    # If the file already exists, add a number to the name
    save_name = save_name.parent / f"{prefix}_{save_name.name}"
    save_name_stem = save_name.stem  # get the stem of the file name to add number to
    while save_name.exists():
        save_name = save_name.parent / f"{save_name_stem}({counter}){save_name.suffix}"
        counter += 1
    save_data.to_csv(save_name, sep=sep, index=False)
    return save_name
