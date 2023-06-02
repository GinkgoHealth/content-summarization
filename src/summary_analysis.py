from pandas import json_normalize  
import pandas as pd
import sys
from file_functions import *
from datetime import datetime
import string
import re

def evaluate_standard(df, column_groups, content_standard, language_standard):
    """
    Evaluate whether content and language ratings in the specified column groups of the given DataFrame meet the
    content and language standards, and create new columns indicating whether they do. For each column group,
    a new column with the specified name will be added to the DataFrame, containing 1 if both the content and
    language ratings meet the standards and 0 otherwise.
    
    Args:
        df (pandas.DataFrame): The DataFrame to evaluate.
        column_groups (list): A list of tuples, each specifying a column group to evaluate. Each tuple should
            contain three strings: the name of the new column to create, the name of the content rating column,
            and the name of the language rating column.
        content_standard (int): The minimum content rating required to meet the content standard.
        language_standard (int): The minimum language rating required to meet the language standard.
        
    Returns:
        pandas.DataFrame: A copy of the input DataFrame with new columns indicating whether content and
        language ratings meet the standards.
    """
    for standard_column, content_rating, language_rating  in column_groups:
        if (df[content_rating] >= content_standard) & (df[language_rating] >= language_standard):
            df[standard_column] = 1
        else:
            df[standard_column] = 0
    return df

def process_sheet(df, content_standard=4, language_standard=4, column_pairs=None):
    """
    Process a spreadsheet by extracting ratings, stripping white spaces, and evaluating whether content and
    language ratings meet specified standards.
    
    Args:
        df (pandas.DataFrame): The DataFrame representing the spreadsheet to process.
        content_standard (int): The minimum content rating required to meet the content standard.
        language_standard (int): The minimum language rating required to meet the language standard.
        column_pairs (list): A list of tuples, each specifying a pair of columns to evaluate. Each tuple should
            contain two strings: the name of the content rating column and the name of the language rating column.
            If None (the default), all column pairs with "content rating" and "language rating" in their names
            will be evaluated.
        
    Returns:
        pandas.DataFrame: A copy of the input DataFrame with ratings extracted, white spaces stripped, and new
        columns added indicating whether content and language ratings meet the standards.
    """

    spreadsheet_columns = [letter for letter in string.ascii_uppercase]+['A'+letter for letter in string.ascii_uppercase]
    processed_df = df.copy()
    processed_df.columns = [f'{spreadsheet_columns[index]}: {column}' for index, column in enumerate(processed_df.columns)]

    # Extract the numbers from ratings
    ratings_columns = [column for column in processed_df.columns if ('rating' in column) | ('top' in column)]
    print(f'Ratings columns (n={len(ratings_columns)}):', ratings_columns)
    processed_df[ratings_columns] = processed_df[ratings_columns].apply(
        lambda x: x.str.extract(r'(\d+)', expand=False))
    processed_df[ratings_columns] = processed_df[ratings_columns].apply(pd.to_numeric, errors='coerce')
    # processed_df[ratings_columns] = processed_df[ratings_columns].astype('Int64')
    print(f'Ratings columns (n={len(processed_df[ratings_columns].columns)}): {[column for column in processed_df[ratings_columns].columns]}')

    # Strip white spaces at start and end of strings
    str_cols = processed_df.select_dtypes(include=['object']).columns
    print(f'String columns (n={len(str_cols)}): {[column for column in str_cols]}')
    processed_df[str_cols] = processed_df[str_cols].apply(lambda x: x.str.strip())
    print('White spaces stripped at start and end of strings')


    if column_pairs == None:
        content_ratings_columns = processed_df.columns[processed_df.columns.str.contains('content rating')]
        language_ratings_columns = processed_df.columns[processed_df.columns.str.contains('language rating')]
    new_column_names = [
        re.sub(r'content rating', 'ratings meet standard', column) for column in content_ratings_columns]
    column_groups = [(
        name, content_rating, language_rating
        ) for name, content_rating, language_rating in (zip(
        new_column_names, content_ratings_columns, language_ratings_columns))
        ]
    processed_df = processed_df.apply(
        evaluate_standard, args=(column_groups,  content_standard, language_standard), axis=1)
    
    return processed_df
