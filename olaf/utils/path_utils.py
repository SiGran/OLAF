import re
from datetime import datetime

from olaf.CONSTANTS import DATE_PATTERN


def natural_sort_key(s: str) -> list:
    """
    Key function for sorting strings in "natural" order.
    Args:
        s: string to sort

    Returns:
        list: list of strings and numbers to sort

    """
    # TODO: this doesn't work with windows file paths it seems
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def save_df_file(clean_df, save_file, header_info):
    counter = 0
    output_stem = save_file.stem
    while save_file.exists():
        # If the file exists, append a number to the filename
        counter += 1
        save_file = save_file.with_name(output_stem + f"({counter})" + save_file.suffix)

    with open(save_file, "w") as f:
        f.write(f"filename = {save_file.name}\n")
        for key, value in header_info.items():
            f.write(f"{key} = {value}\n")
        clean_df.to_csv(f, index=False, lineterminator="\n")
    return


def is_within_dates(dates, folder_name):
    """
    Check if the folder name contains a date that is within the given date range.

    Args:
        dates: Tuple of (start_date, end_date) in string format
        folder_name: String name of folder which might contain a date

    Returns:
        bool: True if folder date is in range, False otherwise
    """
    # Extract date from folder name
    date_match = re.findall(DATE_PATTERN, folder_name)
    if not date_match or len(date_match) != 1:
        return False

    folder_date_str = date_match[0]

    try:
        earliest_date, latest_date = dates

        # Conveart folder to datetime object
        folder_date = datetime.strptime(folder_date_str, "%m.%d.%y")

        # Check if folder date is within range (inclusive)
        return earliest_date <= folder_date <= latest_date

    except (ValueError, IndexError):
        # If any parsing fails, assume not in range
        return False
