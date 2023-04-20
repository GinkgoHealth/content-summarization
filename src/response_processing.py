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

def process_chaining_results(
        chain_results_dict, qna_dict, chatbot_dict, iteration_id, results_type='simple',
        chatbot_id=None, save_df=False, save_chatbot=False,
        csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
        pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles'
        ):
    """
    Merge the qna_dict and chatbot_dict into a single DataFrame. 
    Return the dataframe grouped by rows by qna_dict[iteration_id].columns
    """
    # Create an empty list to store the dataframes
    df_list = []
    iteration_id = chatbot_id if chatbot_id != None else iteration_id
    # Iterate through the chatbot_dict and the simple_summary_dict
    for chatbot_key in chatbot_dict[iteration_id].keys():
        if results_type=='simple':
            results_dict = chatbot_dict[iteration_id][chatbot_key].simple_summary_dict
        else:
            results_dict = chatbot_dict[iteration_id][chatbot_key].relevance_dict
        for iteration_key in results_dict.keys():
            for response_key in results_dict[iteration_key].keys():
                df_list.append(pd.DataFrame(results_dict[iteration_key][response_key]).transpose())
    
    # Concatenate the dataframes into a single dataframe
    new_results = pd.concat(df_list)
    print('New results shape:', new_results.shape)
    
    # Merge the qna_dict and the simple_summaries dataframe
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
    print(f'{"simple summaries" if results_type=="simple" else "added relevance"} dataframe shape:', new_results.shape)
    print([column for column in new_results.columns])
    chain_results_dict[iteration_id] = new_results
    if save_df:
        try:
            save_output(
                chain_results_dict[iteration_id], description=f'prompt_chain_simple_summaries_{results_type}',
                csv_path=csv_path, pickle_path=pickle_path)
            print('DataFrame pickled.')
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} DataFrame')
    if save_chatbot:
        try:
            save_output(
                chatbot_dict[iteration_id], description=f'chaining_bot_{results_type}',
                csv_path=None, pickle_path=pickle_path)
            print('Chaining object (chatbot) pickled.')
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