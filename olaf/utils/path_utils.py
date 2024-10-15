import re


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
