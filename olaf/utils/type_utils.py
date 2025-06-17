import ast


def ensure_list(value):
    """Convert a string representation of a list to an actual list if needed."""
    if isinstance(value, str):
        return ast.literal_eval(value)
    return value
