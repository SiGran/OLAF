from pathlib import Path

import pandas as pd


def read_with_flexible_header(
    file_path: Path,
    expected_columns: tuple = ("degC", "dilution", "INPS_L", "lower_CI", "upper_CI"),
    max_rows: int = 20,
):
    """ """
    header_found = False
    header_lines = []
    i = 0
    with open(file_path, "r") as f:
        skiprows = 0
        while not header_found:
            line = f.readline()
            if not line:  # end of file
                print(f"No columns {expected_columns} found in {file_path}")
                break
            elif tuple(line.strip().split(",")) == expected_columns:
                skiprows = i
                header_found = True
            else:
                header_lines.append(line.strip())
            i += 1

    return header_lines, pd.read_csv(file_path, skiprows=skiprows)


def header_to_dict(header_lines):
    """Convert header lines to a dictionary"""
    if isinstance(header_lines, str):
        header_lines = header_lines.splitlines()
    header_dict = {}
    for line in header_lines:
        if " = " in line:
            key, value = line.split(" = ", 1)
            # Keep track of other header values (use the last file's values)
            header_dict[key] = value
        else:
            # Handle lines that don't match the expected format
            print(f"Unexpected header line format: {line}")
    return header_dict


def unique_dilutions(series):
    """Convert dilution values to integers when possible, handling tuples and lists"""
    unique_vals = series.unique()
    cleaned_vals = set()  # Use a set to collect unique values

    def process_value(val):
        try:
            # First convert to float
            float_val = float(val)
            # Convert to int if it's a whole number
            if float_val.is_integer():
                return int(float_val)
            else:
                return float_val
        except (ValueError, TypeError):
            # Keep as is if not convertible
            return val

    for val in unique_vals:
        if isinstance(val, (tuple, list)):
            # If value is a tuple or list, process each element
            for item in val:
                cleaned_vals.add(process_value(item))
        else:
            # Process scalar value
            cleaned_vals.add(process_value(val))

    # Sort and return as tuple
    return tuple(sorted(cleaned_vals))
