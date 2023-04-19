import os

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
    for filename in os.listdir(folder_path):
        with open(os.path.join(folder_path, filename), 'r', encoding=encoding) as f:
            if subset is None:
                all_files.append(f.read())  # read the entire file
            else:
                all_files.append(f.read(subset))  # read the specified subset of the file
    return create_text_dict(all_files)