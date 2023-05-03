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
import openai

class Chaining:
    """
    Parameters:
    -----------
    text : str
        Text to feed to GPT for summarization.

    Optional parameters:
    --------------------
    system_role : str
        The role of the ChatGPT system in the conversation. Default is "You are an expert at science communication."
    temperature : float
        Controls the randomness of responses. Lower values result in more predictable responses. Default is 0.7.
    n_choices : int
        Number of ChatGPT responses to generate. Default is 5.
    max_tokens : int
        Token limit for ChatGPT response. Default is 1000.
    model : str
        ChatGPT model to use. Default is "gpt-3.5-turbo".
    """

    def __init__(self, text, model="gpt-3.5-turbo", temperature=0.7, max_tokens=1000, 
        system_role="You are an expert at science communication."):
        self.text = text
        self.system_role = system_role
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model

    def create_prompt(self, task, text):
        """
        Creates a prompt for ChatGPT with the given task and text.

        Parameters:
        -----------
        task : str
            The task to include in the ChatGPT prompt.
        text : str
            The text to include in the ChatGPT prompt.

        Returns:
        --------
        messages : list
            A list of dictionaries representing the system and user messages in the prompt.
        """
        system_role = f'{self.system_role}'
        user_input = f"""Given the following text: {text} \n {task}"""
        messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_input},]

        print('\tDone creating prompt')
        return messages

    def gpt(self, messages, n_choices, temperature):
        """
        Sends a request to the ChatGPT API with the given messages.

        Parameters:
        -----------
        messages : list
            A list of dictionaries representing the system and user messages in the prompt.
        n_choices : int
            Number of ChatGPT responses to generate.
        temperature : float
            Controls the randomness of responses. Lower values result in more predictable responses.

        Returns:
        --------
        response : dict
            A dictionary representing the ChatGPT response.
        """
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

    def summarize(self, task, prep_step=None, n_choices=5):
        """
        Generates summaries from the text using ChatGPT.

        Parameters:
        -----------
        task : str
            The task to include in the ChatGPT prompt.
        prep_step : str, optional
            A preparatory step for the task, if applicable.
        n_choices : int, optional
            Number of ChatGPT responses to generate. Default is 5.

        Returns:
        --------
        qna : dict
            A dictionary representing the summarization task and the generated summaries.
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
        self.n_previous_prompts = dict()

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
                    pause_per_request=0
                    ):
        simplify_iteration = len(self.simple_summary_dict) + 1 
        self.n_previous_prompts['simply_summary'] = len(self.simple_summary_dict)
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
                    pause_per_request=0
                    ):
        relevance_iteration = len(self.relevance_dict) + 1 
        self.n_previous_prompts['relevance'] = len(self.relevance_dict)
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
    temperature=0.7, pause_per_request=0, n_choices=5,
    save_outputs=False, filename=None, 
    csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
    pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles',
    json_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\json'
    ):
    """
    Summarize multiple texts using the same prompts.
    Parameters:
        - text_dict (dict) A dictionary containing the text data to be summarized. 
            The keys of the dictionary are the text IDs and the values are the full texts.
        - prep_step, summarize_task (list)
        - qna_dict: Dictionary to store the input and outputs.
        - iteration_id (int, float, or string): Unique ID serving as the key for results in the qna_dict

        iteration_id: int, float or string
            A unique identifier for the current iteration.
        temperature: float, optional (default=0.7)
            The level of "creativity" to use when generating summaries. Higher temperatures will result in more diverse summaries, but may also result in lower quality summaries.
        pause_per_request: int or float, optional (default=0)
            The number of seconds to pause between requests to avoid exceeding API rate limits. Defaults to 0, which means no pause.
        save_outputs: bool, optional (default=False)
            Whether to save the outputs of the summarization process to disk.
        filename: str, optional (default=None)
            The name of the file to save the outputs to. If no filename is specified, a default filename will be used.
        csv_path: str, optional 
            The path to the directory where CSV output files will be saved. Defaults to the 'output' folder in the project directory.
        pickle_path: str, optional 
            The path to the directory where pickle output files will be saved. Defaults to the 'pickles' folder in the project directory.

        Returns:
        --------
        qna_dict: dict
            A dictionary containing the results of the summarization process. The keys of the dictionary are the iteration IDs and the values are pandas dataframes containing the summaries for each text ID

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
                chatbot = Chaining(text, temperature=temperature)
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
                    qna_dict[iteration_id], description='batch_Chaining_summaries',
                    csv_path=csv_path, pickle_path=pickle_path)
                save_instance_to_dict(
                    chaining_bot_dict[iteration_id], 
                    description=f'batch_Chaining_attributes',
                    pickle_path=pickle_path, json_path=json_path
                    )
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
                    )
            else: 
                summary_dict = chaining_bot_dict[text_prompt_key].add_relevance(
                    prompt, audience, n_choices=n_choices, pause_per_request=pause_per_request, 
                    )
            simple_summaries_master_list.append(summary_dict)
  
    simple_summaries_dict[iteration_id] = simple_summaries_master_list
    return simple_summaries_dict
