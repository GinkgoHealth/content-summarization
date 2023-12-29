import re
import string
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
from silvhua_plot import plot_int_bar, plot_proportion

def evaluate_standard(df, column_groups, content_standard, language_standard):
    """
    Evaluates the given DataFrame based on the specified column groups and content and language standards.

    Parameters:
    - df (DataFrame): The DataFrame to be evaluated.
    - column_groups (list): A list of tuples representing the column groups. Each tuple should contain three elements: the standard column name, the content rating column name, and the language rating column name.
    - content_standard (float): The minimum content standard to be considered as "standard".
    - language_standard (float): The minimum language standard to be considered as "standard".

    Returns:
    - df (DataFrame): The updated DataFrame with an additional column indicating whether each row meets the standard or not.
    """
    for standard_column, content_rating, language_rating  in column_groups:
        if (df[content_rating] >= content_standard) & (df[language_rating] >= language_standard):
            df[standard_column] = 1
        else:
            df[standard_column] = 0
    return df

def plot_proportion_abs(df, columns, classification, label=1, height=150):
    """
    Generate a plot of the proportion of a specified label in a given dataframe, and an interactive bar plot.

    Parameters:
        df (pandas.DataFrame): The dataframe to be plotted.
        columns (list): The list of column names to be plotted.
        classification (str): The column name containing the classification labels.
        label (int, optional): The label to be plotted. Defaults to 1.
        height (int, optional): The height of the plots in pixels. Defaults to 150.

    Returns:
        None
    """
    plot_proportion(df, columns, classification, label, height=height)
    plot_int_bar(df, columns, classification, label, height=height)

def process_sheet(df, content_standard=4, language_standard=4, column_pairs=None):
    """
    Processes the AI knowledge library Google sheet by performing various operations on a DataFrame.

    Parameters:
    - df (DataFrame): The input DataFrame to be processed.
    - content_standard (int): The content standard to be used for evaluation. Default is 4.
    - language_standard (int): The language standard to be used for evaluation. Default is 4.
    - column_pairs (list): A list of column pairs to be used for evaluation. If not provided, all columns containing "content rating" and "language rating" will be used.

    Returns:
    - processed_df (DataFrame): The processed DataFrame after applying the specified operations.
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