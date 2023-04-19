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
    Required parameters:
        - text (str): Text to feed to GPT for summarization.

    Optional parameters:
        - system_role (str): ChatGPT parameter. 
            Default is "You are an expert at science communication."
        - temperature (float): ChatGPT parameter. Default is 0.7.
        - n_choices (int): Number of ChatGPT responses to generate. Default is 5.
        - max_tokens (int): Token limit for ChatGPT response.
        - model (str): ChatGPT model to use. Default is "gpt-3.5-turbo".
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
        Creates a prompt for ChatGPT with a given task and text.

        Parameters:
            - task (str): Task to include in ChatGPT prompt.
            - text (str): Text to use in the prompt.

        Returns:
            A list of dictionaries, where each dictionary represents a message in the prompt.
        """
        system_role = f"{self.system_role}"
        user_input = f"""Given the following text: {text} \n {task}"""
        messages = [
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_input},
        ]

        print('\tDone creating prompt')
        return messages

    def gpt(self, messages, n_choices):
        """
        Sends a request to ChatGPT using the provided messages and returns the response.

        Parameters:
            - messages (list of dict): A list of dictionaries, where each dictionary represents a message.
            - n_choices (int): Number of ChatGPT responses to generate.

        Returns:
            The response from ChatGPT.
        """
        print('\tSending request to GPT-3')
        print(f'\t\tRequesting {n_choices} choices using {self.model}')
        openai.api_key = os.getenv('api_openai')
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            n=n_choices
        )
        print('\tDone sending request to GPT-3')
        return response

    def summarize(self, task, prep_step=None, n_choices=5):
        """
        Sends a ChatCompletion request to ChatGPT via the Chaining class and returns the response.

        Parameters:
            - task (str): Task to include in ChatGPT prompt.
            - prep_step (str): Optional string representing a preparation step.
            - n_choices (int): Number of ChatGPT responses to generate. Default is 5.

        Returns:
            A dictionary with the following keys:
                - 'article_title' (str): The title of the summarized article.
                - 'system_role' (str): The role of the system in the ChatGPT prompt.
                - 'model' (str): The ChatGPT model used.
                - 'prep step' (str): Optional
        """
        chatbot = Chaining(self.text)
        prompt = chatbot.create_prompt(task, self.text)
        firstline_pattern = r'\s?(\S*)(\n*)(.+)'
        title = re.match(firstline_pattern, self.text)[0]
        self.qna = dict() 
        self.qna['article_title'] = title
        self.qna['system_role'] = self.system_role
        self.qna['model'] = self.model
        self.qna['prep step'] = prep_step
        self.qna['summarization task'] = task
        self.summaries_dict = dict()
        self.article_title = title
        self.response_regex = r'response_(.*)'
        self.simple_summary_dict = dict()

        try:
            response = chatbot.gpt(prompt, n_choices=n_choices)
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
            self.qna[f'text'] = self.text
            self.summaries_dict['prep_step'] = prep_step
            self.summaries_dict['prompt'] = task
            return self.qna
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('\t**Error with response parsing**')
            return self.qna


    def relevance(self, relevance_task, system_role='You are an expert at science communication.',
                    model="gpt-3.5-turbo", temperature=0.0, n_choices=1, max_tokens=1000, 
                    simplify_iteration=None, pause_per_request=20
                    ):
        self.simple_summary_dict[simplify_iteration] = dict()
        if simplify_iteration == None:
            simplify_iteration = 1
        summaries_keys = [key for key in self.summaries_dict.keys() if re.match(self.response_regex, key)]
        print('summaries_keys: \n\t', summaries_keys)
        for key in summaries_keys:
            new_key = re.sub(self.response_regex, rf'simple_summary\1', key)
            print(f'\t\t...Preparing to summarize {key}')
            simplify_prompt = self.create_prompt(simplify_task, self.summaries_dict[key])
            try:
                response = self.gpt(simplify_prompt, n_choices)
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                print('\t**API request failed for `.simplify()`**')
                return self.qna
            try:
                for index, choice in enumerate(response.choices):
                    simple_summary_option = f'{new_key}_option{"{:02d}".format(index+1)}'
                    self.simple_summary_dict[simplify_iteration].setdefault(simple_summary_option, {})
                    self.simple_summary_dict[simplify_iteration][simple_summary_option] = choice["message"]["content"]                    
                    print(f'\t...Summary given')
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
                self.simple_summary_dict[simplify_iteration][new_key] = response
                print(f'\t...Error parsing response for summary request')
            print(f'[.simplify()] Sleeping {pause_per_request} sec to avoid exceeding API rate limit')
            time.sleep(pause_per_request) # Account for API rate limit of 3 API requests/limit 
        self.simple_summary_dict[simplify_iteration]['summary'] = self.summaries_dict
        self.simple_summary_dict[simplify_iteration]['simplify task'] = simplify_task
        return self.simple_summary_dict


def batch_summarize_chain(text_dict, prep_step, summarize_task, qna_dict, chaining_bot_dict, iteration_id, n_choices=5,
    prompt_column='prompt', pause_per_request=20,
    save_outputs=False, filename=None, append_version=False,
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
                temp_qna_dict[key][index] = chatbot.summarize(task=task, prep_step=prep_step, n_choices=n_choices)
                chaining_bot_dict[iteration_id][f'text{key}_prompt{"{:02d}".format(index)}'] = chatbot
                print('\t...Success!')
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

def prompt_chaining_dict(simplify_prompts, simple_summaries_dict, chaining_bot_dict, iteration_id,
    summary_iteration_id=None, n_choices=None, pause_per_request=20,
    prompt_column='simplify', simplify_iteration=None, save_outputs=False,
    csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
    pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles'
    ):
    """
    Simplify or add context to a summary.
    """
    summary_iteration_id = summary_iteration_id if summary_iteration_id else iteration_id
    print('summary_iteration_id:', summary_iteration_id)
    if n_choices == None:
        n_choices = 1 if prompt_column == 'simplify' else 5
    print('n_choices:', n_choices)
    if type(simplify_prompts) == str:
        simplify_prompts = [simplify_prompts]
    elif type(simplify_prompts) == pd.core.frame.DataFrame:
        simplify_prompts = [prompt for prompt in simplify_prompts[prompt_column].unique() if len(prompt) >1]
    else:
        simplify_prompts = list(set([prompt for prompt in simplify_prompts if len(prompt) >1]))
    simple_summaries_master_list = []
    for text_prompt_key in chaining_bot_dict.keys():
        print(f'**{text_prompt_key}')
        # simple_summaries_master_dict[text_prompt_key] = dict()

        for index, prompt in enumerate(simplify_prompts):
            relevance_iteration=index if len(simplify_prompts) > 1 else simplify_iteration
            print(f'\t...Prompt: {prompt}, iteration {relevance_iteration}')
            if prompt_column == 'simplify':
                summary_dict = chaining_bot_dict[text_prompt_key].simplify(
                    prompt, n_choices=n_choices, pause_per_request=pause_per_request, 
                    simplify_iteration=index if len(simplify_prompts) > 1 else simplify_iteration
                    )
            else: 
                summary_dict = chaining_bot_dict[text_prompt_key].add_relevance(
                    prompt, n_choices=n_choices, pause_per_request=pause_per_request, 
                    relevance_iteration=index if len(simplify_prompts) > 1 else simplify_iteration
                    )
            simple_summaries_master_list.append(summary_dict)
  
    simple_summaries_dict[iteration_id] = simple_summaries_master_list
    return simple_summaries_dict