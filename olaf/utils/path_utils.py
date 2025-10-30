import re
from collections import defaultdict
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
    # note: this might have different behavior on Linux than Windows.
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def find_latest_file(file_paths):
    """
    Find the latest version of a file from a list of files that may have (N) version indicators.
    Files without version numbers are treated as version 0.

    Args:
        file_paths: List of Path objects to examine

    Returns:
        Path object of the latest version file
    """
    if not file_paths:
        return None

    def get_version(path):
        """Extract version number from filename, return -1 for base filename without number."""
        match = re.search(r"\((\d+)\)(?:\.[^.]+)?$", str(path))
        return int(match.group(1)) if match else -1

    # Group files by base name (removing version numbers)
    base_files = {}
    for file_path in file_paths:
        # Remove the (N) part if it exists to get base name
        base_name = re.sub(r"\(\d+\)(?:\.[^.]+)?$", file_path.suffix, str(file_path))
        if base_name not in base_files:
            base_files[base_name] = []
        base_files[base_name].append(file_path)

    # For each group, find the file with highest version number
    latest_files = []
    for files in base_files.values():
        latest_files.append(max(files, key=get_version))

    # If multiple base names, return the most recently modified
    if len(latest_files) > 1:
        return max(latest_files, key=lambda x: x.stat().st_mtime)
    return latest_files[0]


def save_df_file(clean_df, save_file, header_info, index=False):
    """Save a pandas DataFrame to CSV with custom header metadata.

    If the target file already exists, appends a number suffix (N) to create
    a unique filename. The header metadata is written as key-value pairs
    before the CSV data.

    Args:
        clean_df: Pandas DataFrame to save.
        save_file: Path object for the output file.
        header_info: Dictionary of metadata to write as header (key=value format).
        index: Whether to include DataFrame index in CSV (default: False).

    Returns:
        None. File is written to disk.
    """
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
        clean_df.to_csv(f, index=index, lineterminator="\n")
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

        # Convert folder to datetime object
        folder_date = datetime.strptime(folder_date_str, "%m.%d.%y")

        # Check if folder date is within range (inclusive)
        return earliest_date <= folder_date <= latest_date

    except (ValueError, IndexError):
        # If any parsing fails, assume not in range
        return False


def sort_files_by_date(file_paths):
    """Sort and group file paths by date extracted from filename.

    Extracts dates from filenames using DATE_PATTERN and groups files
    by date. Also extracts trailing numbers from filenames (before .csv)
    to track file versions.

    Args:
        file_paths: List of Path objects to sort.

    Returns:
        Dictionary mapping date strings to lists of (file_path, number) tuples,
        where number is the trailing version number (0 if not present).
    """
    # Group files by date
    files_by_date = defaultdict(list)
    for file_path in file_paths:
        date_match = re.findall(DATE_PATTERN, file_path.name)
        if date_match and len(date_match) == 1:  # skip if more dates match
            date = date_match[0]
            # Find the trailing number if it exists
            number_match = re.search(r"(\d+)\.csv$", file_path.name)
            number = int(number_match.group(1)) if number_match else 0
            files_by_date[date].append((file_path, number))
    return files_by_date
