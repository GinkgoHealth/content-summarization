import pandas as pd
import pickle
from datetime import datetime
import json
import sys

# 2022-10-27 17:02 Update the sampling function to avoid loading entire dataframe.
def load_csv(filename,filepath,column1_as_index=False,truncate=None, usecols=None, sep=','):
    """
    Load a csv file as a dataframe using specified file path copied from windows file explorer.
    Back slashes in file path will be converted to forward slashes.
    Arguments:
    - filepath (raw string): Use the format r'<path>'.
    - filename (string).
    - colum1_as_index (bool): If true, take the first column as the index. 
        Useful when importing CSV files from previously exported dataframes.

    Returns: dataframe object.
    """
    filename = f'{filepath}/'.replace('\\','/')+filename
    df = pd.read_csv(filename, usecols=usecols, sep=sep)
    if column1_as_index==True:
        df.set_index(df.columns[0], inplace=True)
        df.index.name = None
    print('Dataframe shape: ',df.shape)
    print('DataFrame columns:', [col for col in df.columns])
    print('\tTime completed:', datetime.now())

    if truncate:
        return df.sample(n=truncate,random_state=0)
    else:
        return df

def save_csv(df,filename,path=None,append_version=False, index=True):
    """
    Export dataframe to CSV.
    Parameters:
    - df: Dataframe variable name.
    - filename: Root of the filename.
    - filepath (raw string): Use the format r'<path>'. If None, file is saved in same director.
    - append_version (bool): If true, append date and time to end of filename.
    """
    if path:
        path = f'{path}/'.replace('\\','/')
    if append_version == True:
        filename+=datetime.now().strftime('%Y-%m-%d_%H%M')
    df.to_csv(path+filename+'.csv', index=index)
    print('File saved: ',path+filename+'.csv')
    print('\tTime completed:', datetime.now())


def savepickle(model,filename, ext='sav', path=None,append_version=False):
    """
    Export object as a pickle.
    Parameters:
    - model: Model variable name.
    - filename: Root of the filename.
    - extension: Extension to append (do not include dot as it will be added)
    - filepath (raw string): Use the format r'<path>'. If None, file is saved in same director.
    - append_version (bool): If true, append date and time to end of filename.
    """
    if path:
        path = f'{path}/'.replace('\\','/')
    if append_version == True:
        filename+=datetime.now().strftime('%Y-%m-%d_%H%M')
    with open (path+filename+'.'+ext, 'wb') as fh:
        pickle.dump(model, fh)
    print('File saved: ',path+filename+'.'+ext)
    print('\tTime completed:', datetime.now())

def loadpickle(filename,filepath):
    """
    Load a pickled model using specified file path copied from windows file explorer.
    Back slashes in file path will be converted to forward slashes.
    Arguments:
    - filepath (raw string): Use the format r'<path>'.
    - filename (string).
    
    Returns saved object.
    """
    filename = f'{filepath}/'.replace('\\','/')+filename
    object = pickle.load(open(filename, 'rb'))
    print('\tTime completed:', datetime.now())
    if type(object) == pd.core.frame.DataFrame:
        print('Dataframe shape: ',object.shape)
        print('DataFrame columns:', [col for col in object.columns])
    if type(object) == dict:
        print('Dictionary keys:', [key for key in object.keys()])
    return object

def save_output(df, filename=None, description=None, append_version=True, iteration_id=None, index=False,
    csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\CSV',
    pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles'
    ):
    """
    Save an Python object as both pickle and CSV. Automatically create filename using date and time 
    if not provided.
    
    """
    if description:
        filename = f'{description}_{datetime.now().strftime("%Y-%m-%d_%H%M")}'
        append_version = False
    elif filename == None:
        filename = f'{datetime.now().strftime("%Y-%m-%d_%H%M")}_outputs'
        append_version = False
    if iteration_id:
        filename += f'_{"{:02d}".format(iteration_id)}'
    try:
        savepickle(df, filename=filename, path=pickle_path, append_version=append_version)
        print('\tObject saved as pickle')
    except Exception as error:
        print('Unable to save pickle')
        print(f'\t{error}')
    if (type(df) == pd.core.frame.DataFrame) & (csv_path != None):
        save_csv(df, filename=filename, path=csv_path, append_version=append_version, index=index)
        print('\tDataFrame saved as CSV')
    elif (type(df) == dict) & (csv_path != None):
        try:
            save_csv(pd.DataFrame(df), filename=filename, path=csv_path, append_version=append_version)
            print('\tDictionary converted to CSV')
        except:
            print('\tUnable to save CSV')


def save_to_json(obj, filename=None, description='output_dictionary', append_version=False,
    path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\json'
    ):
    """
    Save Python object as a JSON file.
    Parameters:
    - obj: Python object to be saved.
    - filename: Root of the filename.
    - path (raw string): Use the format r'<path>'. If None, file is saved in same directory as script.
    - append_version (bool): If true, append date and time to end of filename.
    """
    if description:
        filename = f'{description}_{datetime.now().strftime("%Y-%m-%d_%H%M")}'
        append_version = False
    elif filename == None:
        filename = f'{datetime.now().strftime("%Y-%m-%d_%H%M")}_outputs'
        append_version = False
    if path:
        path = f'{path}/'.replace('\\','/')
    if append_version:
        filename += f'_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}'
    filename += '.json'
    with open(path+filename, 'w') as f:
        json.dump(obj, f)
    print(f'Object saved as JSON: {path}/{filename}')

def save_instance_to_dict(chatbot_dict_iteration, filename=None, description='batch_Chaining_attributes', 
        ext='sav', save_json=True, append_version=True, 
        pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles',
        json_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\jsons'
    ):
    """
    Convert the class instance to a dictionary whose values are the instance attributes.
    Export object as a pickle and/or JSON file.
    Parameters:
    - chatbot_dict_iteration: A dictionary whose items are class instances.
    - filename (str): Root of the filename.
    - description (str): Parameter in `save_output` function.
    - ext (str): Extension to append (do not include dot as it will be added). Default is 'sav'. If None, 
        object is not pickled.
    - pickle_path, json_path (raw string): Use the format r'<path>'. If None, file is saved in same director.
    - append_version (bool): If true, append date and time to end of filename.
    """
    chatbot_dictionary = {}


    for key, item in chatbot_dict_iteration.items():
        chatbot_dictionary[key] = dict()
        print(key)
        for attr, value in vars(item).items():
            print(f'\t{attr}')
            chatbot_dictionary[key][attr] = value
        chatbot_dictionary[key]['date_created'] = f'{datetime.now().strftime("%Y-%m-%d_%H%M")}'
    if ext:
        try:
            save_output(
                chatbot_dictionary, filename=filename, description=description,
                append_version=append_version, csv_path=None, pickle_path=pickle_path
            )
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to pickle chatbot dictionary')
        print('Dictionary keys:', chatbot_dictionary.keys())
    if save_json==True:
        try:
            save_to_json(
                chatbot_dictionary, 
                filename=filename, description=description,
                append_version=append_version, path=json_path
            )
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save chatbot dictionary to JSON')
    return chatbot_dictionary

def load_json(filename, filepath):
    """
    Load a JSON file using specified file path copied from windows file explorer.
    Back slashes in file path will be converted to forward slashes.

    Arguments:
    - filepath (raw string): Use the format r'<path>'.
    - filename (string).
    """
    filename = f'{filepath}/'.replace('\\','/')+filename
    with open(filename) as file:
        return json.load(file)

def save_article_dict(article_dict, path, description='scraped_articles_dict', append_version=True,
    save_pickle=True, save_json=False, to_csv=False):
    """
    Save a dictionary of articles to a file. Default behaviour is to save as a pickle only.
    Parameters:
        - article_dict (dict): Dictionary of articles.
        - path (str): Path to save the file.
        - description (str): Description of the file for the filename.
        - append_version (bool): If True, append the date to the filename.
        - save_pickle (bool): If True, save the dictionary as a pickle file.
        - save_json (bool): If True, save the dictionary as a JSON file.
        - to_csv (bool): If True, convert the dictionary to a DataFrame to save as a CSV file.
    """
    if save_pickle == True:
        savepickle(article_dict, filename=f'{description}_', path=path, append_version=append_version)
    if save_json == True:
        save_to_json(article_dict, description=description, path=path, append_version=append_version)
    if to_csv == True:
        save_csv(pd.DataFrame(article_dict).transpose().drop(columns=['text']), path=path, filename=f'{description}_',
            index=True, append_version=append_version)