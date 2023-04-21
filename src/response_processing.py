import pandas as pd
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\portfolio-projects\online-PT-social-media-NLP\src")
from silvhua import *
from datetime import datetime
import os
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
import traceback
import re
import string
from collections import OrderedDict

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
                description=f'batch_Chaining_attributes_{results_type}',
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
        path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles'
    ):
    """
    Export object as a pickle.
    Parameters:
    - model: Model variable name.
    - filename: Root of the filename.
    - extension: Extension to append (do not include dot as it will be added)
    - filepath (raw string): Use the format r'<path>'. If None, file is saved in same director.
    - append_version (bool): If true, append date and time to end of filename.
    """
    chatbot_dictionary = {}


    for key, item in chatbot_dict_iteration.items():
        chatbot_dictionary[key] = dict()
        print(key)
        for attr, value in vars(item).items():
            print(f'\t{attr}')
            chatbot_dictionary[key][attr] = value
    if ext:
        try:
            save_output(
                chatbot_dictionary, filename=filename, description=description,
                append_version=append_version, csv_path=None, pickle_path=path
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
                append_version=append_version, path=path
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
        print(type(empty_columns)) #### delete this
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
                merged_df, description=f'prompt_chain_summaries_and_relevance',
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