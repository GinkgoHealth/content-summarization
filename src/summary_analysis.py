from pandas import json_normalize  
import pandas as pd
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\portfolio-projects\online-PT-social-media-NLP\src")
from silvhua import *
from datetime import datetime
import string

def process_sheet(df):
    """
    See 2023-04-25 Notebook for usage
    """
    spreadsheet_columns = [letter for letter in string.ascii_uppercase]+['A'+letter for letter in string.ascii_uppercase]
    processed_df = df.copy()
    processed_df.columns = [f'{spreadsheet_columns[index]}: {column}' for index, column in enumerate(processed_df.columns)]

    # Extract the numbers from ratings
    ratings_columns = [column for column in processed_df.columns if 'rating' in column]
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
    
    return processed_df
