import pandas as pd
import numpy as np


def split_and_rename(row):
    """
    Splits a string in a row by ' > ' and returns a Series with new column names.

    Args:
    row (str): A string representing ranked choices separated by ' > '.

    Returns:
    pd.Series: A pandas Series where each element is a choice, indexed by 'choice_n'.
    """
    # Split the row by ' > ' to separate choices
    choices = row.split(' > ')
    # Create a Series from the choices, naming columns as 'choice_1', 'choice_2', etc.
    return pd.Series(choices, index=[f'choice_{i + 1}' for i in range(len(choices))])


def remove_first_four_chars(s):
    """
    Removes the first four characters from each element in a pandas Series.

    Args:
    s (pd.Series): A pandas Series with string elements.

    Returns:
    pd.Series: A Series with the first four characters removed from each string.
    """
    # Apply a lambda function to remove the first four characters if the element is a string and not NaN
    return s.apply(lambda x: x[4:] if pd.notna(x) and len(x) > 4 else x)


def contains_all_elements(row, elements_list):
    """
    Checks if all elements in a provided list are present in a DataFrame row.

    Args:
    row (pd.Series): A row of a DataFrame.
    elements_list (list): A list of elements to check for in the row.

    Returns:
    bool: True if all elements are found in the row, False otherwise.
    """
    # Check if all elements in elements_list are present in the row
    return all(elem in row.values for elem in elements_list)


def shift_choices(row, eliminated_candidate):
    """
    Removes an eliminated candidate from a row and shifts the remaining choices to the left.

    Args:
    row (pd.Series): A row from a DataFrame representing ranked choices.
    eliminated_candidate (str): The candidate to be removed from the row.

    Returns:
    list: Updated row with the eliminated candidate removed and choices shifted left.
    """
    # Remove the eliminated candidate and shift the remaining choices to the left
    filtered_choices = [choice for choice in row if choice != eliminated_candidate]
    # Fill the remaining positions with NaN to maintain row length
    return filtered_choices + ['NaN'] * (len(row) - len(filtered_choices))


# Custom function to lowercase only specific strings
def conditional_lowercase(val, strings_to_lowercase):
    if isinstance(val, str) and val.lower() in strings_to_lowercase:
        return val.lower()
    return val

