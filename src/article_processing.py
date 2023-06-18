import re
from IPython import display

def create_text_dict(text, text_dict=None):
    """
    Creates a dictionary of text data.

    Args:
        text (str or list): The text data to include in the dictionary. If a string is provided,
            it will be stored as a single value in the dictionary. If a list is provided, each
            item in the list will be stored as a separate value in the dictionary.
        text_dict (dict, optional): An existing dictionary to which the text data will be added.
            If not specified, a new dictionary will be created. Defaults to None.

    Returns:
        dict: A dictionary of text data, where the keys are numerical identifiers starting from 1
            and the values are the text data.

    Example:
        text = ['This is the first text.', 'This is the second text.']
        text_dict = create_text_dict(text)
    """
    if text_dict == None:
        text_dict = dict()
        text_id = 1
    else:
        text_id = len(text_dict) + 1
    if type(text) == str:
    
        text_dict[text_id] = text
    elif type(text) == list:
        for value in text:
            text_dict[text_id] = value
            text_id += 1
    print(f'\nKeys for text_dict: {text_dict.keys()}\n')
    return text_dict

def create_text_dict_from_folder(folder_path, encoding='ISO-8859-1', subset=None):
    """
    Creates a dictionary of text data from all files in the specified folder.

    Args:
        folder_path (str): The path to the folder containing the text files.
        encoding (str, optional): The encoding of the text files. Defaults to 'ISO-8859-1'.
        subset (int, optional): The number of bytes to read from each file. If not specified,
            the entire file will be read. Defaults to None.

    Returns:
        dict: A dictionary of text data, where the keys are numerical identifiers starting from 1
            and the values are the contents of the corresponding files.

    Example:
        folder_path = './text_files'
        text_dict = create_text_dict_from_folder(folder_path, encoding='UTF-8', subset=100)
    """
    import os
    all_files = []
    files_to_get = [file for file in os.listdir(folder_path) if file.endswith(".txt")]
    for filename in files_to_get:
        with open(os.path.join(folder_path, filename), 'r', encoding=encoding) as f:
            if subset is None:
                all_files.append(f.read())  # read the entire file
            else:
                all_files.append(f.read(subset))  # read the specified subset of the file

    return create_text_dict(all_files)

def grab_references(
        kl_df, references_df, type='new', kl_reference_column='B: article', references_df_column='Reference', 
        filter_string=None):
    """
    Grab references from the references dataframe based on if if there is already knowledge library content
    referencing it (or not). Default is to return new references.
    
    Args:
    - kl_df: a DataFrame containing the values to be used for filtering the references DataFrame
    - references_df: a DataFrame containing the references to be filtered
    - type: a string indicating whether to return new or existing references, defaults to 'new'. 
        If any other value, returns existing references.
    - kl_reference_column: a string indicating the name of the column in kl_df to be used for filtering, defaults to 'B: article'
    - references_df_column: a string indicating the name of the column in references_df to be used for filtering, defaults to 'Reference'
    - filter_string: a string indicating the filter criteria, defaults to None.
        This is the string passed to the .query() method. Example: '`Reference Rank` <= 2'.
        Column names with spaces or other special characters must be enclosed in backticks.
    
    Returns:
    - A DataFrame containing the new (or existing) references based on the specified filter criteria.

    Example usage:
        filter_string = '`Reference Rank` == 1'
        grab_references(df, references, type='new', filter_string=filter_string)
    """
    
    # Create a list of unique article titles in kl_df[kl_reference_column]
    kl_article_titles = kl_df[kl_reference_column].str.replace(r'(.+) \d{4} article .*', r'\1', regex=True)
    kl_article_titles = kl_article_titles.str.replace(r'(.+) \d{4} section .*', r'\1', regex=True)
    kl_article_titles = kl_article_titles.str.replace(r'(.+) article .*', r'\1', regex=True)
    kl_article_titles = kl_article_titles.str.replace(r'(.+) section .*', r'\1', regex=True)
    kl_article_titles = kl_article_titles.str.strip()
    kl_article_titles = kl_article_titles.str.lower().str.replace(':', '').str.replace('\s+', ' ', regex=True).str.replace('-', ' ').unique().tolist()
    print(f'Number of unique articles summarized: {len(kl_article_titles)}')
    # Filter the references DataFrame based on the article titles in kl_df[kl_reference_column]. Strip colon, extra white space, and hyphens.
    references_filter = references_df[references_df_column].str.lower().str.replace(
        ':', '').str.replace('\s+', ' ', regex=True).str.replace('-', ' ').apply(
        lambda x: any(article in x.lower() for article in kl_article_titles))    
    if type == 'new':
        # Create a list of article titles in references that do not correspond to article titles in kl_df[kl_reference_column]
        new_references = references_df.loc[~references_filter, references_df_column].str.lower().str.replace(':', '').str.replace('\s+', ' ', regex=True).str.replace('-', ' ').unique().tolist()
    else:
        new_references = references_df.loc[references_filter, references_df_column].str.lower().str.replace(':', '').str.replace('\s+', ' ', regex=True).str.replace('-', ' ').unique().tolist()
    
    # Filter the references DataFrame to show only the rows corresponding to new_references
    new_references_df = references_df.loc[references_df[references_df_column].str.lower().str.replace(':', '').str.replace('\s+', ' ', regex=True).str.replace('-', ' ').isin(new_references)]
    
    # If filter_column and filter_string are provided, filter the new_references_df based on the provided criteria
    if filter_string is not None:
        # Filter the new_references_df based on the provided criteria
        new_references_df = new_references_df.query(f"{filter_string}")
    
    print(f'Number of {type} references where {filter_string}: {len(new_references_df)}')
    
    return new_references_df

def trim_text(text, regex=r'(.*)'):
    try:
        processed = re.search(regex, text, re.DOTALL).group(1)
        html_display = display.HTML(processed)
    except: 
        print('Unable to parse article text')
        processed = '<Error parsing article text>' 
        html_display = processed
    return processed, html_display

def text_dict_from_web(article_dict, header=2, to_display=0,
        regex_str='.*<h\d>Abstract</h\d>.*(?:Introduction)?.*(<h\d.*?>Introduction</h\d>.*References)<.*'
        ):
    """
    Create a text dictionary from a dictionary containing web-scraped articles.

    Parameters:
        article_dict (dict): Values of each dictionary item are a dictionary representing the data from a 
            single article: 'url', 'text', and 'title'.

    Returns:
        text_dict: Dictionary where each item is a string of the text of an article, starting with the title.
    """
    regex_str = regex_str.replace('\d', f'{header}')
    regex = rf'{regex_str}'
    print(f'Regex pattern: {regex}')
    text_dict = dict()
    display_dict = dict()
    if type(to_display) != list:
        to_display = [to_display] 
    for article_key in article_dict:
        trimmed_text, display = trim_text(article_dict[article_key]['text'], regex)
        text_dict[article_key] = f"{article_dict[article_key]['title']}\n\n{trimmed_text}"
        if article_key in to_display:
            display_dict[article_key] = display
    print(f'text_dict keys: {[key for key in text_dict.keys()]}')
    return text_dict, display_dict