import pandas as pd
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\portfolio-projects\online-PT-social-media-NLP\src")
from silvhua import *
from datetime import datetime
import os
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
import traceback
import time
import re
from itertools import product

class Chaining:
    """
    Requrired paramaters:
        - text (str): Text to feed to GPT for summarization.

    Optional parameters
        - system_role (str): ChatGPT parameter. 
            Default is "You are an expert at science communication."
        - temperature (float): ChatGPT parameter. Default is 0.7.
        - n_choices (int): Number of ChatGPT responses to generate. Default is 5.
        - max_tokens (int): Token limit for ChatGPT response.
        - model (str): ChatGPT model to use. Default is "gpt-3.5-turbo".
    """

    def __init__(self, text, model="gpt-3.5-turbo", temperature=0.7, max_tokens=1000, 
        system_role = "You are an expert at science communication."):
        self.text = text
        self.system_role = system_role
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
    
    def create_prompt(self, task, text):
        system_role = f'{self.system_role}'
        user_input = f"""Given the following text: {text} \n {task}"""
        messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_input},]

        print('\tDone creating prompt')
        return messages

    def gpt(self, messages, n_choices, temperature):
        print('\tSending request to GPT-3')
        print(f'\t\tRequesting {n_choices} choices using {self.model}')
        openai.api_key = os.getenv('api_openai')
        response = openai.ChatCompletion.create(
            model=self.model, messages=messages, 
            temperature=temperature, 
            max_tokens=self.max_tokens,
            n=n_choices
            )
        print('\tDone sending request to GPT-3')
        return response

    def summarize(self, task, prep_step=None, n_choices=5
        ):
        """
        SH 2023-04-11 12:18: Same as the user-defined `reply` function, but re-written as a class method.
        Send a ChatCompletion request to ChatGPT via the Chaining class.

        Requrired paramaters:
            - task (str): Task to include in ChatGPT prompt.
            - text (str): Text to feed to GPT for summarization.

        Optional parameters
            - system_role (str): ChatGPT parameter. 
                Default is "You are an expert at science communication."
            - temperature (float): ChatGPT parameter. Default is 0.7.
            - n_choices (int): Number of ChatGPT responses to generate. Default is 5.
            - max_tokens (int): Token limit for ChatGPT response.
            - model (str): ChatGPT model to use. Default is "gpt-3.5-turbo".
        """
        chatbot = Chaining(self.text)
        full_task = f'{prep_step} {task}'
        prompt = chatbot.create_prompt(full_task, self.text)
        firstline_pattern = r'\s?(\S*)(\n*)(.+)'
        title = re.match(firstline_pattern, self.text)[0]
        self.qna = dict() 
        self.qna['article_title'] = title
        self.qna['system_role'] = self.system_role
        self.qna['model'] = self.model
        self.qna[f'text'] = self.text
        self.qna['prep step'] = prep_step
        self.qna['summarization task'] = task
        self.qna['full summarization task'] = full_task
        self.summaries_dict = dict()
        self.article_title = title
        self.response_regex = r'response_(.*)'
        self.simple_summary_dict = dict()
        self.relevance_dict = dict()

        try:
            response = chatbot.gpt(prompt, n_choices=n_choices, temperature=self.temperature)
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('\t**API request failed for `.summarize()`**')
            return self.qna
        try:
            for index, choice in enumerate(response.choices):
                self.summaries_dict[f'response_{"{:02d}".format(index+1)}'] = choice["message"]["content"]
            self.qna.setdefault('summary', [])
            self.qna['summary'].extend([value for value in self.summaries_dict.values()])
            self.summaries_dict['prep_step'] = prep_step
            self.summaries_dict['task'] = task
            self.summaries_dict['prompt'] = full_task
            return self.qna
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('\t**Error with response parsing**')
            return self.qna


    def simplify(self, simplify_task, audience, 
                    model="gpt-3.5-turbo", temperature=0.0, n_choices=1, 
                    # simplify_iteration=None, 
                    pause_per_request=20
                    ):
        simplify_iteration = len(self.simple_summary_dict) + 1 
        self.simple_summary_dict[simplify_iteration] = dict()
        if simplify_iteration == None:
            simplify_iteration = 1
        full_simplify_task = f'{simplify_task} {audience}'
        print('simplify_iteration: ', simplify_iteration)
        print('Task:', full_simplify_task)
        summaries_keys = [key for key in self.summaries_dict.keys() if re.match(self.response_regex, key)]
        print('summaries_keys: \n\t', summaries_keys)
        for key in summaries_keys:
            new_key = re.sub(self.response_regex, rf'simple_summary\1', key)
            print(f'\t\t...Preparing to summarize {key}')
            simplify_prompt = self.create_prompt(full_simplify_task, self.summaries_dict[key])
            try:
                response = self.gpt(simplify_prompt, n_choices=n_choices, temperature=temperature)
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                print('\t**API request failed for `.simplify()`**')
                return self.qna
            try:
                self.simple_summary_dict[simplify_iteration][key] = dict()
                for index, choice in enumerate(response.choices):
                    self.simple_summary_dict[simplify_iteration][key][index] = {
                        'simple summary choice': index+1, 
                        'simplify task': simplify_task,
                        'audience': audience,
                        'full simplify task': f'{simplify_task} {"for" if audience else ""} {audience}',
                        'simple summary': choice["message"]["content"],
                        'original summary': self.summaries_dict[key]
                    }
                    print(f'\t...Summary given')
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                self.simple_summary_dict[simplify_iteration][new_key] = response
                print(f'\t...Error parsing response for summary request')
            if pause_per_request > 0:
                print(f'[.simplify()] Sleeping {pause_per_request} sec to avoid exceeding API rate limit')
                time.sleep(pause_per_request)
        return self.simple_summary_dict
    
    def add_relevance(self, relevance_task, audience, 
                    model="gpt-3.5-turbo", temperature=0.0, n_choices=1, summary_type='original',
                    # relevance_iteration=None, 
                    pause_per_request=20
                    ):
        relevance_iteration = len(self.relevance_dict) + 1 
        self.relevance_dict[relevance_iteration] = dict()
        if relevance_iteration == None:
            relevance_iteration = 1
        full_relevance_task = f'{relevance_task} {audience}'
        print('relevance_iteration: ', relevance_iteration)
        print('Task:', full_relevance_task)
        if summary_type=='original':
            summaries_keys = [key for key in self.summaries_dict.keys() if re.match(self.response_regex, key)]
            summary_regex = self.response_regex
        else:
            self.simple_summary_response_regex = r'simple_summary_(.*)'
            summaries_keys = [key for key in self.summaries_dict.keys() if re.match(self.simple_summary_response_regex, key)]
            summary_regex = self.simple_summary_response_regex
        print('summaries_keys: \n\t', summaries_keys)
        input_summary_dict = self.summaries_dict if summary_type=='original' else self.simple_summary_dict
        for key in summaries_keys:
            new_key = re.sub(summary_regex, rf'relevance_\1', key)
            print(f'\t\t...Preparing to add relevance to {key}')
            relevance_prompt = self.create_prompt(full_relevance_task, input_summary_dict[key])
            try:
                response = self.gpt(relevance_prompt, n_choices=n_choices, temperature=temperature)
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                print('\t**API request failed for `.add_relevance()`**')
                return self.qna
            try:
                self.relevance_dict[relevance_iteration][key] = dict()
                for index, choice in enumerate(response.choices):
                    self.relevance_dict[relevance_iteration][key][index] = {
                        'relevance choice': index+1, 
                        'relevance task': relevance_task,
                        'audience': audience,
                        'full relevance task': full_relevance_task,
                        'relevance statement': choice["message"]["content"],
                        'preceding summary': input_summary_dict[key]
                    }
                    print(f'\t...Relevance statement given')
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                self.relevance_summary_dict[relevance_iteration][new_key] = response
                print(f'\t...Error parsing response for relevance request')
            if pause_per_request > 0:
                print(f'[.add_relevance()] Sleeping {pause_per_request} sec to avoid exceeding API rate limit')
                time.sleep(pause_per_request)
        return self.relevance_dict
    
def batch_summarize_chain(text_dict, prep_step, summarize_task, qna_dict, chaining_bot_dict, iteration_id, 
    temperature=0.7, pause_per_request=0,
    save_outputs=False, filename=None, 
    csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
    pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles'
    ):
    """
    Summarize multiple texts using the same prompts.
    Parameters:
        - prep_step, summarize_task (list)
        - qna_dict: Dictionary to store the input and outputs.
        - iteration_id (int, float, or string): Unique ID serving as the key for results in the qna_dict
        - prompt_column (str): Name of the column in the prompts_df containing the user input.
    """
    temp_qna_dict = dict()
    qna_dfs_list = []
    prompts_df = pd.DataFrame(product(prep_step, summarize_task), 
        columns=['prep_step', 'summarize_task'])

    chaining_bot_dict[iteration_id] = dict()
    for key in text_dict:
        text = text_dict[key]
        temp_qna_dict[key] = dict()
        for index in prompts_df.index:
            print(f'**Text #{key} prompt #{index} of {prompts_df.index.max()}**')
            task = prompts_df.loc[index, 'summarize_task']
            prep_step = prompts_df.loc[index, 'prep_step']
            try:
                print('Creating Chaining class instance')
                chatbot = Chaining(text)
                print('Chaining class instance created')
                temp_qna_dict[key][index] = chatbot.summarize(
                    task=task, prep_step=prep_step, n_choices=n_choices,
                    )
                chaining_bot_dict[iteration_id][f'text{key}_prompt{"{:02d}".format(index)}'] = chatbot
                print('\t...Success!')
                if pause_per_request > 0:
                    print(f'[batch_summarize()] Sleeping {pause_per_request} sec to avoid exceeding API rate limit')
                    time.sleep(pause_per_request) # Account for API rate limit of 3 API requests/limit 
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                print('\t...Error making chatbot request')
                break
        
        try:
            updated_qna_dict = (temp_qna_dict[key])
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('Error concatenating prompts DataFrame')
            return temp_qna_dict, chaining_bot_dict
        qna_dfs_list.append(updated_qna_dict)
    try:
        qna_dict[iteration_id] = pd.concat([
            pd.DataFrame(
                data, index=[choice for choice in range(1, len(data['summary'])+1)]
            ) for dictionary in qna_dfs_list for data in dictionary.values()
        ])
        qna_dict[iteration_id].reset_index(inplace=True, names=['choice'])
        print('DataFrame shape:', qna_dict[iteration_id].shape)
        if save_outputs:
            try:
                save_output(
                    qna_dict[iteration_id], description='prompt_chain_experiment',
                    csv_path=csv_path, pickle_path=pickle_path)
                save_output(
                    chaining_bot_dict[iteration_id], description='chaining_bot_dict',
                    csv_path=None, pickle_path=pickle_path)
            except:
                print('[prompt_chaining_dict()] Unable to save outputs')
    except Exception as error:
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        print("An error occurred on line", lineno, "in", filename, ":", error)
        qna_dict[iteration_id] = qna_dfs_list
        print('Error creating DataFrame; dictionary returned instead')
    return qna_dict, chaining_bot_dict

def prompt_chaining_dict(simplify_prompts, audience, simple_summaries_dict, chaining_bot_dict, iteration_id,
    summary_iteration_id=None, n_choices=None, pause_per_request=0,
    prompt_column='simplify', 
    # simplify_iteration=None
    ):
    """
    Simplify or add context to a summary.
    """
    summary_iteration_id = summary_iteration_id if summary_iteration_id else iteration_id
    print('summary_iteration_id:', summary_iteration_id)
    prompts_df = pd.DataFrame(product(simplify_prompts, audience), columns=[prompt_column, 'audience'])
    if n_choices == None:
        n_choices = 1 if prompt_column == 'simplify' else 5
    print('n_choices:', n_choices)

    simple_summaries_master_list = []
    for text_prompt_key in chaining_bot_dict.keys():
        print(f'**{text_prompt_key}')

        for index in prompts_df.index:
            prompt = prompts_df.loc[index, prompt_column]
            audience = prompts_df.loc[index, 'audience']
            if prompt_column == 'simplify':
                summary_dict = chaining_bot_dict[text_prompt_key].simplify(
                    prompt, audience, n_choices=n_choices, pause_per_request=pause_per_request, 
                    # simplify_iteration=index if len(simplify_prompts) > 1 else simplify_iteration
                    )
            else: 
                summary_dict = chaining_bot_dict[text_prompt_key].add_relevance(
                    prompt, audience, n_choices=n_choices, pause_per_request=pause_per_request, 
                    # relevance_iteration=index if len(simplify_prompts) > 1 else simplify_iteration
                    )
            simple_summaries_master_list.append(summary_dict)
  
    simple_summaries_dict[iteration_id] = simple_summaries_master_list
    return simple_summaries_dict


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
                results_dict[iteration_id], description='prompt_chain_simple_summaries',
                csv_path=csv_path, pickle_path=pickle_path)
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
                chatbot_dict[iteration_id], description='chaining_bot',
                csv_path=None, pickle_path=pickle_path)
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print(f'Unable to save {"simple summaries" if results_type=="simple" else "added relevance"} chatbot')
            
    return chain_results_dict