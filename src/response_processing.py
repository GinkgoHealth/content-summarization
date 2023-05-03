import pandas as pd
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
from silvhua import *
from datetime import datetime
import os
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
import traceback
import re
import string
from collections import OrderedDict
from summary_chain import Chaining

def process_chaining_results(
        chain_results_dict, qna_dict, chatbot_dict, iteration_id, results_type='simple',
        empty_columns=None,
        chatbot_id=None, save_df=False, save_chatbot=False,
        csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
        pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles',
        json_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\json'
        ):
    """
    Merge the qna_dict and chatbot_dict into a single DataFrame. 
    Return the dataframe grouped by rows by qna_dict[iteration_id].columns
    """
    df_list = []
    iteration_id = chatbot_id if chatbot_id != None else iteration_id
    for chatbot_key in chatbot_dict[iteration_id].keys():
        if results_type=='simple':
            results_dict = chatbot_dict[iteration_id][chatbot_key].simple_summary_dict
        else:
            results_dict = chatbot_dict[iteration_id][chatbot_key].relevance_dict
        for iteration_key in results_dict.keys():
            for response_key in results_dict[iteration_key].keys():
                df_list.append(pd.DataFrame(results_dict[iteration_key][response_key]).transpose())
    
    new_results = pd.concat(df_list)
    print('New results shape:', new_results.shape)
    
    new_results = qna_dict[iteration_id].merge(
        new_results, how='right', 
        right_on=f'{"original" if results_type=="simple" else "preceding"} summary', 
        left_on='summary'
    )
    if results_type=='simple':
        columns = [
            'article_title',
            'choice',
            'system_role',
            'model',
            'text',
            'prep step',
            'summarization task',
            'full summarization task',
            'summary',
            'simple summary choice',
            'audience',
            'simplify task',
            'full simplify task',
            'simple summary'
        ]
    else:
        columns= [
            'article_title',
            'choice',
            'system_role',
            'model',
            'text',
            'prep step',
            'summarization task',
            'full summarization task',
            'summary',
            'relevance choice',
            'audience',
            'relevance task',
            'full relevance task',
            'relevance statement'
        ]
    new_results = new_results[columns]

    if empty_columns:
        if (type(empty_columns) != dict) & (type(empty_columns) != OrderedDict):
            empty_columns = {
                'original summary content rating': 'k',
                'original summary language rating': 'l',
                'top summary': 'm',
            }
        print('\nColumns before adding empty columns:', [column for column in new_results.columns])
        print('Inserting empty columns...', end='\n\t')
        spreadsheet_columns = [letter for letter in string.ascii_uppercase]+['A'+letter for letter in string.ascii_uppercase]
        alphabet_dict = {char:idx for idx, char in enumerate(spreadsheet_columns)}
        for column_name, column_number in empty_columns.items():
            empty_column_loc = alphabet_dict[empty_columns[column_name].upper()] -1
            new_results.insert(loc=empty_column_loc, column=column_name, value='')
            print(f'{empty_columns[column_name].upper()} ({empty_column_loc}): {column_name}', end=', ')
        new_results.columns = [
            f'{spreadsheet_columns[index+1]}: {column}' for index, column in enumerate(new_results.columns)
            ]

    print(f'** {"simple summaries" if results_type=="simple" else "added relevance"} dataframe shape:', new_results.shape)
    print([column for column in new_results.columns])
    chain_results_dict[iteration_id] = new_results
    if save_df:
        try:
            save_output(
                chain_results_dict[iteration_id], description=f'prompt_chain_simple_summaries_{results_type}',
                csv_path=csv_path, pickle_path=pickle_path)
            print('')
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} DataFrame')
    if save_chatbot:
        try:
            print('Saving Chaining object (chatbot)...')
            save_instance_to_dict(
                chatbot_dict[iteration_id], 
                description=f'batch_Chaining_attributes',
                pickle_path=pickle_path, json_path=json_path
                )
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} chatbot')
            
    return chain_results_dict

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
    - ext (str): Extension to append (do not include dot as it will be added). Default is 'sav'.
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

def merge_chaining_results(
        qna_dict, chatbot_dict, 
        simple_summaries_dict, relevance_dict, iteration_id, 
        empty_columns=None, pivot=True, validate=None,
        chatbot_id=None, save_df=False, save_chatbot=False,
        csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
        pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles',
        json_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\json'
        ):
    """
    Merge the summaries, simple summaries, added relevance into a single DataFrame. 
    Parameters:
        - qna_dict, chatbot_dict (dict): Dictionaries of qna DataFrames and Chaining instances
        - simple_summaries_dict: dictionary of simple summaries DataFrames
        - relevance_dict: dictionary of added relevance DataFrames
        - iteration_id: iteration ID of the chatbot
        - empty_columns (dict, OrderedDict, int, bool): dictionary of empty columns to insert into the DataFrame. 
            Keys are the column names, values are the column letters in the spreadsheet.
            If True but dictionary is not passed, a default dictionary will be used
            based on Google sheet as of 2023-04-19.
        - pivot (bool): whether to pivot the DataFrame so that 
            multiple added relevance statements are in the same row.
        - validate (str): Argument to pass to pd.merge() to validate the merge.
        - chatbot_id (int): ID of the chatbot to use if different from iteration_id.
        - save_df (bool): whether to save the DataFrame.
        - save_chatbot (bool): whether to save the chatbot.
        - csv_path (str): path to save the csv file. If None, no CSV is saved.
        - pickle_path (str): path to save the pickle file. If None, no pickle is saved.

    """
    iteration_id = chatbot_id if chatbot_id != None else iteration_id
    simple_summary_df = process_chaining_results(
        simple_summaries_dict, qna_dict, chatbot_dict, iteration_id,
        results_type='simple', empty_columns=None,
        chatbot_id=chatbot_id, 
        save_df=False, save_chatbot=False,
        csv_path=csv_path, pickle_path=pickle_path, json_path=json_path
        )[iteration_id]
    relevance_df = process_chaining_results(
        relevance_dict, qna_dict, chatbot_dict, iteration_id, 
        results_type='relevance', chatbot_id=chatbot_id, 
        save_df=False, save_chatbot=save_chatbot,
        csv_path=csv_path, pickle_path=pickle_path, json_path=json_path
        )[iteration_id]
    
    if pivot == False:
        validate=None
        # Identify common columns
        common_columns = list(set(simple_summary_df.columns) & set(relevance_df.columns))
        common_columns.remove('audience')

        print('Merging on common columns:', common_columns)
        merged_df = simple_summary_df.merge(
            relevance_df, how='outer', suffixes=(' simplify', ' relevance'),
            on=common_columns,
            validate=validate
            )
    else:
        relevance_pivot_df = relevance_df.pivot(
            columns=['audience'],
            values='relevance statement',
            index=['summary', 'relevance task']
        ).reset_index()
        merged_df = simple_summary_df.merge(
            relevance_pivot_df, how='outer', suffixes=(' simplify', ' relevance'),
            on=['summary'],
            validate='m:1' if validate else None
        )
    if empty_columns:
        if (type(empty_columns) != dict) & (type(empty_columns) != OrderedDict):
            empty_columns = {
                'original summary content rating': 'k',
                'original summary language rating': 'l',
                'top summary': 'm',
                'simple summary content rating': 's',
                'simple summary language rating': 't',
                'top simple summary': 'u',
                'full add relevance task': 'w',
                'added relevance content rating': 'y',
                'added relevance language rating': 'z',
                'top added relevance': 'aa',
                'add relevance task (seniors)': 'AB',
                'full add relevance task (seniors)': 'AC',
            }
        print('\nColumns before adding empty columns:', [column for column in merged_df.columns])
        print('Inserting empty columns...', end='\n\t')
        spreadsheet_columns = [letter for letter in string.ascii_uppercase]+['A'+letter for letter in string.ascii_uppercase]
        alphabet_dict = {char:idx for idx, char in enumerate(spreadsheet_columns)}
        for column_name in empty_columns.keys():
            empty_column_loc = alphabet_dict[empty_columns[column_name].upper()] -1
            merged_df.insert(loc=empty_column_loc, column=column_name, value='')
            print(f'{empty_columns[column_name].upper()} ({empty_column_loc}): {column_name}', end=', ')

        merged_df.columns = [f'{spreadsheet_columns[index+1]}: {column}' for index, column in enumerate(merged_df.columns)]

    if save_df:
        try:
            save_output(
                merged_df, description=f'prompt_chain_summaries',
                csv_path=csv_path, pickle_path=pickle_path)
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} DataFrame')
    
    print('\nMerged DataFrame shape:', merged_df.shape)
    print('Merged DataFrame columns: ', [column for column in merged_df.columns])
    return merged_df

def revive_chatbot(chatbot):
    """
    Convert the dictionary of a chatbot attributes into a Chaining object.
    """
    new_chatbot = Chaining(chatbot['text'])
    print(f'Article title: {chatbot["article_title"]}')
    for key in chatbot.keys():
        setattr(new_chatbot, key, chatbot[key])
        print(f'\tNew chatbot attribute added: {key}')
        if type(getattr(new_chatbot, key)) == dict:
            print(f'\t\tAttribute dictionary keys: {[attr for attr in getattr(new_chatbot, key)]}')
    if not hasattr(chatbot[key], 'n_previous_prompts'):
        
        print(f'\tNew chatbot attribute added: n_previous_prompts')
        setattr(new_chatbot, 'n_previous_prompts',  dict())

    else:
        print(f'\tUpdating `n_previous_prompts`...')

    summaries_keys = [key for key in new_chatbot.summaries_dict.keys() if re.match(new_chatbot.response_regex, key)]
    new_chatbot.n_previous_prompts['summaries'] = len(summaries_keys)
    new_chatbot.n_previous_prompts['simple_summary'] = len(new_chatbot.simple_summary_dict.keys())
    new_chatbot.n_previous_prompts['relevance'] = len(new_chatbot.relevance_dict.keys())

    print(f'\t\tPrevious number of prompts:')
    print(f'\t\t\tOriginal summaries: {len(summaries_keys)} {[key for key in summaries_keys]}')
    print(f'\t\t\tSimple summaries: {len(new_chatbot.simple_summary_dict.keys())}')
    print(f'\t\t\tAdded relevance: {len(new_chatbot.relevance_dict.keys())}')
    
    return new_chatbot


def revive_chatbot_dict(chatbot_dict, texts='all'):
    """
    Convert the dictionary of dictionaries of chatbot attributes into a dictionary of Chaining objects.

    Parameters:
        - chatbot_dict (dict): dictionary of dictionaries of chatbot attributes.
        - texts (list or 'all'): list of integers corresponding to the text prompts to revive. 
            If 'all', all text prompts will be revived.

    See "2023-05-01 test new prompts" notebook for example usage.
    """
    if texts == 'all':
        text_prompts_to_revive = [text for text in chatbot_dict.keys()]
    elif isinstance(texts, list):
        text_prompts_to_revive = [
            text_prompt for text_prompt in chatbot_dict.keys() for text in texts if f'{text}_' in text_prompt]
    else:
        raise TypeError("The `texts` parameter must be 'all' or a list of integers")

    new_chatbot_dict = {text_prompt: revive_chatbot(chatbot_dict[text_prompt]) for text_prompt in text_prompts_to_revive}
    print(f'\n\nNew chatbot dict keys: {[key for key in new_chatbot_dict]}')
    return new_chatbot_dict

def process_chaining_results2(
        chain_results_dict, chatbot_dict, iteration_id, results_type='simple',
        empty_columns=None, pivot=True, validate=None,
        chatbot_id=None, save_df=False, save_chatbot=False, 
        csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
        pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles',
        json_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\json'
        ):
    """
    Create a dataframe of new 'simple' or 'relevance' summaries from a Chaining object.
    Merge it with the original summaries DataFrame.

    Parameters:
        - chain_results_dict (dict): dictionary of DataFrames.
        - qna_dict (dict): dictionary of QnA DataFrames.
        - chatbot_dict (dict): dictionary of Chaining objects.
        - iteration_id (int, float, or string): iteration_id (dict key) of the chatbot_dict to process.
        - results_type (str): 'simple' or 'relevance'. Default is 'simple'.
        - empty_columns (Bool, int, or dict): dictionary of empty columns to add to the DataFrame. 
            If True or 1, default dictionary is used.
            If False or 0, no empty columns are added.
        - pivot (Bool): whether to pivot the relevance summaries DataFrame. Default is True.
        - validate (str): Argument to pass to pd.merge() to validate the merge.
        - chatbot_id (int, float, or string): chatbot_id (dict key) of the chatbot_dict to process.
        - save_df, save_chatbot (Bool): whether to save the DataFrame and chatbot_dict.

    """
    df_list = []
    qna_dfs_list = []
    iteration_id = chatbot_id if chatbot_id != None else iteration_id
    for chatbot_key in chatbot_dict[iteration_id].keys():
        print(f'Processing {chatbot_key}...')
        try: 
            n_previous_prompts = chatbot_dict[iteration_id][chatbot_key].previous_n_prompts[results_type]
            print(f'\tNumber of previous {results_type} prompts: {n_previous_prompts}')
        except:
            n_previous_prompts = 0
            print(f'No previous {results_type} prompts for {chatbot_key}')
            
        qna_dfs_list.append(pd.DataFrame(chatbot_dict[iteration_id][chatbot_key].qna))

        if results_type=='simple':
            total_n_prompts = len(chatbot_dict[iteration_id][chatbot_key].simple_summary_dict)
            results_dict = dict()
            for prompt_number in range(n_previous_prompts+1, total_n_prompts+1):
                results_dict[prompt_number] = chatbot_dict[iteration_id][chatbot_key].simple_summary_dict[prompt_number]
            chatbot_dict[iteration_id][chatbot_key].simple_summary_dict
        else:
            total_n_prompts = len(chatbot_dict[iteration_id][chatbot_key].relevance_dict)
            results_dict = dict()
            for prompt_number in range(n_previous_prompts+1, total_n_prompts+1):
                results_dict[prompt_number] = chatbot_dict[iteration_id][chatbot_key].relevance_dict[prompt_number]
        for iteration_key in results_dict.keys():
            response_keys = sorted([text_prompt_key for text_prompt_key in results_dict[iteration_key].keys()])
            print(f'\tAppending results for {iteration_key}: ', end='')
            for response_key in response_keys:
                df_list.append(pd.DataFrame(results_dict[iteration_key][response_key]).transpose())
                print(f'{response_key}, ', end='')
            print('')

    
    new_results = pd.concat(df_list)
    qna_df = pd.concat(qna_dfs_list)
    print(f'Original summaries DataFrame shape: {qna_df.shape}')
    print(f'Original summaries Dataframe columns: {qna_df.columns}')
    print('New results shape:', new_results.shape)
    
    original_summary_columns = [
        'article_title',
        # 'choice',
        'system_role',
        'model',
        'text',
        'prep step',
        'summarization task',
        'full summarization task',
        'summary',
    ]
    pivot = False if results_type=='simple' else pivot
    if (pivot == False) or (results_type=='simple'):
        new_results = qna_df[original_summary_columns].merge(
            new_results, how='right', 
            right_on=f'{"original" if results_type=="simple" else "preceding"} summary', 
            left_on='summary'
        )
        if results_type=='simple':
            columns = [
                'article_title',
                # 'choice',
                'system_role',
                'model',
                'text',
                'prep step',
                'summarization task',
                'full summarization task',
                'summary',
                'simple summary choice',
                'audience',
                'simplify task',
                'full simplify task',
                'simple summary'
            ]
        else:
            columns= [
                'article_title',
                'choice',
                'system_role',
                'model',
                'text',
                'prep step',
                'summarization task',
                'full summarization task',
                'summary',
                'relevance choice',
                'audience',
                'relevance task',
                'full relevance task',
                'relevance statement'
            ]
        print(f'New results columns: {new_results.columns}')
        new_results = new_results[columns]
    else:
        new_results_pivot_df = new_results.pivot(
            columns=['audience'],
            values='relevance statement',
            index=['preceding summary', 'relevance task']
        ).reset_index()
        print(f'Shape of pivoted dataframe: {new_results_pivot_df.shape}')
        new_results = qna_df[original_summary_columns].merge(
            new_results_pivot_df, how='outer', suffixes=(' original', ' relevance'),
            left_on='summary',
            right_on=f'{"original" if results_type=="simple" else "preceding"} summary',
            validate='m:1' if validate else None
        ).drop(columns=['preceding summary'])
        print(f'Merged DataFrame shape: {new_results.shape}')
        new_results.drop_duplicates(inplace=True)
        print(f'Duplicate rows dropped. Shape: {new_results.shape}')

    if empty_columns:
        if pivot == False:
            if (type(empty_columns) != dict):
                if results_type=='simple':
                    empty_columns = {
                        "choice numnber": "C",
                        "original summary content rating": "K",
                        "original summary language rating": "L",
                        "top summary": "M",
                    }
                else:
                    empty_columns = {
                        "choice numnber": "C",
                        "original summary content rating": "K",
                        "original summary language rating": "L",
                        "top summary": "M",
                        "simplify audience": "O",
                        "simplify task": "P",
                        "full simplify task": "Q",
                        "simple summary": "R",
                        "simple summary content rating": "S",
                        "simple summary language rating": "T",
                        "top simple summary": "U",
                    }
        else:           
            if (type(empty_columns) != dict):
                empty_columns = {
                    "choice numnber": "C",
                        "original summary content rating": "K",
                    "original summary language rating": "L",
                    "top summary": "M",
                    "simple summary choice": "N",
                    "simplify audience": "O",
                    "simplify task": "P",
                    "full simplify task": "Q",
                    "simple summary": "R",
                    "simple summary content rating": "S",
                    "simple summary language rating": "T",
                    'top simple summary': 'u',
                    'full add relevance task': 'w',
                    'added relevance content rating': 'y',
                    'added relevance language rating': 'z',
                    'top added relevance': 'aa',
                    'add relevance task (seniors)': 'AB',
                    'full add relevance task (seniors)': 'AC',
                }
        print(f'Merged DataFrame shape: {new_results.shape}')
        print('\nColumns before adding empty columns:', [column for column in new_results.columns])
        print('Inserting empty columns...', end='\n\t')
        spreadsheet_columns = [letter for letter in string.ascii_uppercase]+['A'+letter for letter in string.ascii_uppercase]
        alphabet_dict = {char:idx for idx, char in enumerate(spreadsheet_columns)}
        for column_name, column_number in empty_columns.items():
            empty_column_loc = alphabet_dict[empty_columns[column_name].upper()] -1
            new_results.insert(loc=empty_column_loc, column=column_name, value='')
            print(f'{empty_columns[column_name].upper()} ({empty_column_loc}): {column_name}', end=', ')
        new_results.columns = [
            f'{spreadsheet_columns[index+1]}: {column}' for index, column in enumerate(new_results.columns)
            ]

    print(f'\n** {"simple summaries" if results_type=="simple" else "added relevance"} dataframe shape:', new_results.shape)
    print([column for column in new_results.columns])
    chain_results_dict[iteration_id] = new_results
    try:
        original_summary_time = next(iter(chatbot_dict[iteration_id].values())).date_created
    except:
        original_summary_time = 'previous_summaries'
    print(f'Original summary time: {original_summary_time}')
    if save_df:
        try:
            save_output(
                chain_results_dict[iteration_id], description=f'batch_Chaining_attributes_{original_summary_time}_append_{results_type}',
                csv_path=csv_path, pickle_path=pickle_path)
            print('')
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} DataFrame')
    if save_chatbot:
        try:
            print('Saving Chaining object (chatbot)...')
            save_instance_to_dict(
                chatbot_dict[iteration_id], 
                description=f'batch_Chaining_attributes_{original_summary_time}_append_{results_type}',
                pickle_path=pickle_path, json_path=json_path
                )
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} chatbot')
            
    return chain_results_dict