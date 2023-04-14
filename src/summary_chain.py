import pandas as pd
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\portfolio-projects\online-PT-social-media-NLP\src")
from silvhua import *
from datetime import datetime
import os
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
from summarization import Chatbot, reply
import traceback
import time
import re

class Chaining:

    def __init__(self, text):
        self.text = text

    def summarize(self, task, model="gpt-3.5-turbo", temperature=0.7, n_choices=5, max_tokens=1000,
          text_key=['text_discussion'],
        system_role = "You are an expert at science communication."
        ):
        """
        SH 2023-04-11 12:18: Same as the user-defined `reply` function, but re-written as a class method.
        Send a ChatCompletion request to ChatGPT via the Chatbot class.

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
        chatbot = Chatbot(self.text,
            system_role=system_role, model=model, temperature=temperature, n_choices=n_choices,
            max_tokens=max_tokens
            )
        prompt = chatbot.create_prompt(task)
        firstline_pattern = r'\s?(\S*)(\n*)(.+)'
        title = re.match(firstline_pattern, self.text)[0]
        self.qna = dict() 
        self.qna['article_title'] = title
        self.qna['system_role'] = system_role
        self.qna['prompt'] = task
        self.qna['model'] = model
        self.summaries_dict = dict()
        self.article_title = title
        self.response_regex = r'response_(.*)'

        try:
            response = chatbot.gpt(prompt)
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('\t**API request failed**')
            return self.qna
        try:
            for index, choice in enumerate(response.choices):
                self.qna[f'response_{"{:02d}".format(index+1)}'] = choice["message"]["content"]
                self.summaries_dict[f'response_{"{:02d}".format(index+1)}'] = choice["message"]["content"]
            self.qna[f'text'] = self.text
            return self.qna
        except:
            print('\t**Error with response parsing**')
            return self.qna


    def simplify(self, simplify_task, system_role='You are an expert at science communication.',
                    model="gpt-3.5-turbo", temperature=0.0, n_choices=1, max_tokens=1000, 
                    simplify_iteration=None, pause_per_request=20
                    ):
        self.simplify_bot_dict = dict()
        self.simple_summary_dict = dict()
        if simplify_iteration == None:
            simplify_iteration = 1
        for key, summary in self.summaries_dict.items():
            new_key = re.sub(self.response_regex, rf'simple_summary\1_prompt{str(simplify_iteration)}', key)
            print(f'\t\t...Preparing to summarize {key}')
            self.simplify_bot_dict[new_key] = Chatbot(
                summary, system_role=system_role,
                model=model, temperature=temperature, n_choices=n_choices, max_tokens=max_tokens
                )
            simplify_prompt = self.simplify_bot_dict[new_key].create_prompt(simplify_task)
            try:
                for index, choice in enumerate(self.simplify_bot_dict[new_key].gpt(simplify_prompt).choices):
                    self.simple_summary_dict[f'{new_key}_option{"{:02d}".format(index+1)}'] = choice["message"]["content"]
                    print(f'\t...Summary given')
            except:
                self.simple_summary_dict[new_key] = self.simplify_bot_dict[new_key].gpt(simplify_prompt)
                print(f'\t...Error parsing response for summary request')
            print(f'[.simplify()] Sleeping {pause_per_request} sec to avoid exceeding API rate limit')
            time.sleep(pause_per_request) # Account for API rate limit of 3 API requests/limit 
        self.simple_summary_dict['simplify_task'] = simplify_task
        self.qna = {**self.qna, **self.simple_summary_dict}
        try:
            self.qna.update({'text': self.qna.pop('text')})
        except:
            pass
        return self.simple_summary_dict
    
    def add_relevance(self, task, system_role='You are an expert at science communication.',
                    model="gpt-3.5-turbo", temperature=0.0, n_choices=1, max_tokens=1000, 
                    relevance_iteration=None, pause_per_request=20
                    ):
        self.relevance_bot_dict = dict()
        self.relevance_dict = dict()
        if relevance_iteration == None:
            relevance_iteration = 1
        for key, summary in self.summaries_dict.items():
            new_key = re.sub(self.response_regex, rf'relevance\1_prompt{str(relevance_iteration)}', key)
            print(f'\t\t...Preparing to summarize {key}')
            self.relevance_bot_dict[new_key] = Chatbot(
                summary, system_role=system_role,
                model=model, temperature=temperature, n_choices=n_choices, max_tokens=max_tokens
                )
            relevance_prompt = self.relevance_bot_dict[new_key].create_prompt(task)
            try:
                for index, choice in enumerate(self.relevance_bot_dict[new_key].gpt(relevance_prompt).choices):
                    self.relevance_dict[f'{new_key}_option{"{:02d}".format(index+1)}'] = choice["message"]["content"]
                    print(f'\t...Relevance given')
            except:
                try:
                    self.relevance_dict[new_key] = self.relevance_bot_dict[new_key].gpt(relevance_prompt).choices[0]["message"]["content"]
                    print(f'\t...First relevance response given')
                except:
                    self.relevance_dict[new_key] = self.relevance_bot_dict[new_key].gpt(relevance_prompt)
                    print(f'\t...Error parsing response for added relevance request')
            print(f'[.add_relevance()] Sleeping {pause_per_request} sec to avoid exceeding API rate limit')
            time.sleep(pause_per_request) # Account for API rate limit of 3 API requests/limit 
        self.relevance_dict[f'relevance_task{"{:02d}".format(relevance_iteration)}'] = task
        self.qna = {**self.qna, **self.relevance_dict}
        try:
            self.qna.update({'text': self.qna.pop('text')})
        except:
            pass
        return self.relevance_dict

def batch_summarize_chain(text_dict, prompts_df, qna_dict,  chaining_bot_dict, iteration_id, n_choices=5,
    prompt_column='prompt', pause_per_request=20,
    save_outputs=False, filename=None, append_version=False,
    csv_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
    pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output\pickles'
    ):
    """
    Summarize multiple texts using the same prompts.
    Parameters:
        - prompts_df: DataFrame containing the prompts.
        - qna_dict: Dictionary to store the input and outputs.
        - iteration_id (int, float, or string): Unique ID serving as the key for results in the qna_dict
        - prompt_column (str): Name of the column in the prompts_df containing the user input.

    """
    temp_qna_dict = dict()
    prompts_df = prompts_df.reset_index(drop=True)
    qna_dfs_list = []
    chaining_bot_dict[iteration_id] = dict()
    for key in text_dict:
        text = text_dict[key]
        temp_qna_dict[key] = dict()
        for index, input in prompts_df[prompt_column].items():
            print(f'**Text #{key} prompt #{index} of {prompts_df.index.max()}**')
            try:
                chatbot = Chaining(text)
                temp_qna_dict[key][index] = chatbot.summarize(input, n_choices=n_choices)
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
            prompts_df = prompts_df.drop(prompt_column)
        except:
            pass
        try:
            updated_qna_dict = pd.concat([
                pd.DataFrame(temp_qna_dict[key]),
                prompts_df.transpose()
            ])
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('Error concatenating prompts DataFrame')
            return temp_qna_dict, chaining_bot_dict
        try:
            qna_dfs_list.append(updated_qna_dict)
            qna_dict[iteration_id] = pd.concat(qna_dfs_list, axis=1)
            if save_outputs:
                try:
                    append_version = append_version if filename else False
                    filename = filename if filename else f'{datetime.now().strftime("%Y-%m-%d_%H%M")}_prompt_experiments_{"{:02d}".format(iteration_id)}'
                    savepickle(qna_dict[iteration_id], filename=filename, path=pickle_path, append_version=append_version)
                    save_csv(qna_dict[iteration_id], filename=filename, path=pickle_path, append_version=append_version)
                except:
                    print('Unable to save outputs')
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('Error concatenating DataFrames')
    return qna_dict, chaining_bot_dict

def prompt_chaining_dict(simplify_prompts, qna_chain_dict, chaining_bot_dict, iteration_id,
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
    simple_summaries_master_dict = dict()
    simple_summaries_df = pd.DataFrame()
    for column, text_prompt_key in enumerate(chaining_bot_dict):
        print(f'**{text_prompt_key}')
        simple_summaries_master_dict[text_prompt_key] = dict()

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
            simple_summaries_master_dict[text_prompt_key] = {**simple_summaries_master_dict[text_prompt_key], **summary_dict}
        try:
            simple_summaries_df[column] = pd.DataFrame([
                pd.Series(value, name=key) for key, value in simple_summaries_master_dict[text_prompt_key].items()
            ])   
        except Exception as error:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            print("An error occurred on line", lineno, "in", filename, ":", error)
            print('Unable to create results DataFrame')
            
            qna_chain_dict[iteration_id+0.001] = simple_summaries_master_dict
    try:
        qna_chain_dict[summary_iteration_id].columns = [i for i in range(len(qna_chain_dict[summary_iteration_id].columns))]
        temp_qna_chain_dict = pd.concat([
            qna_chain_dict[summary_iteration_id], 
            simple_summaries_df
            ])
        qna_chain_dict[iteration_id] = temp_qna_chain_dict
        print(f"{'Simple summaries' if prompt_column=='simplify' else 'Article relevance for user'} added to original DataFrame")
        if save_outputs:
            try:
                save_output(
                    qna_chain_dict[iteration_id], description='prompt_chain_experiment',
                    csv_path=csv_path, pickle_path=pickle_path)
            except:
                print('[prompt_chaining_dict()] Unable to save outputs')
    except Exception as error:
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        print("An error occurred on line", lineno, "in", filename, ":", error)
        print('Unable to concatenate simple summary DataFrame to original DataFrame')
        qna_chain_dict[iteration_id+0.001] = simple_summaries_master_dict

    return qna_chain_dict