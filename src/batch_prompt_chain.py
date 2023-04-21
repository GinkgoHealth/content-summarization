import sys
import pandas as pd
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\custom_python")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\portfolio-projects\online-PT-social-media-NLP\src")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
from summary_chain import *
from response_processing import *
from article_processing import create_text_dict_from_folder
from silvhua import *
from datetime import datetime
import openai
import os
import re
from itertools import product
import time
import string

# Create prompt lists
prep_step = [
    # "Take the key points to",
    "Take the key points and numerical descriptors to",
    # ""
]
summarize_task = [
    # "Summarize the article in under 300 characters",
    "Summarize for a LinkedIn post",
    # "Summarize for a tweet",
    "Summarize in an engaging way",
    "Describe the interesting points to your coworker at the water cooler"
    # "Summarize the article for a Tiktok post"
]
simple_simplify_task = [
    # "Use terms a 12-year-old can understand.",
    "Assume your audience has no science background.",
    # "Use a fun tone."
    # "Include the most interesting findings.",
    # "Include the key take-aways for the reader.",
    # "Include the implications of the article."
    # "Include the most interesting findings.",
    # "Include the key take-aways for the reader.",
    # "Include the implications of the article."
]
no_audience = ['']

user_simplify_task = [
    "Use language appropriate for",
    # "Use terms a 12-year-old can understand.",
]
simplify_audience = [
    # "",
    # "a lay audience",
    "people without a science background",
]
user_relevance_task = [
    # "Add 1-2 sentences to make this relevant for",
    "Write this so it is relevant for",
    # "Add 1-2 sentences to make this relevant for older adults."
    # "Once you are done, add 1-2 sentences to make this relevant for older adults.",
]
relevance_audience = [
    # "lay audience",
    # "",
    "seniors",
    "people who enjoy sports"
]

# Set parameters
iteration_id = 1
n_choices = 5
pause_per_request=0
summary_iteration_id = iteration_id
chatbot_id = iteration_id

# Create text dictionary
folder_path = '../text/2023-04-20'
encoding='ISO-8859-1'
subset=None

text_dict = create_text_dict_from_folder(folder_path, encoding=encoding, subset=subset)

qna_dict = dict()
chatbot_dict = dict()
simple_summaries_dict = dict()
relevance_dict = dict()

# Create initial summaries
qna_dict, chaining_dict = batch_summarize_chain(
    text_dict, prep_step, summarize_task, qna_dict, chatbot_dict, 
    n_choices=n_choices, pause_per_request=pause_per_request,
    iteration_id=iteration_id
    )

time.sleep(pause_per_request)

# Create simple summaries
simplify_prompts = user_simplify_task
audience = simplify_audience
simple_summaries = prompt_chaining_dict(simplify_prompts, audience, simple_summaries_dict, 
    chaining_dict[iteration_id], iteration_id,
    n_choices=1, pause_per_request=pause_per_request, summary_iteration_id=summary_iteration_id
    )

# simple_summaries_dict = process_chaining_results(
#     simple_summaries_dict, qna_dict, chatbot_dict, iteration_id,
#     results_type='simple', chatbot_id=chatbot_id, 
#     save_df=True, save_chatbot=False
#     )

# Add relevance
relevance_prompts = user_relevance_task
relevance = prompt_chaining_dict(relevance_prompts, relevance_audience, relevance_dict, 
    chaining_dict[summary_iteration_id], iteration_id, prompt_column='relevance', 
    n_choices=1, pause_per_request=pause_per_request, summary_iteration_id=summary_iteration_id
    )
# relevance_dict = process_chaining_results(
#     relevance_dict, qna_dict, chatbot_dict, iteration_id, 
#     results_type='relevance', chatbot_id=chatbot_id, 
#     save_df=True, save_chatbot=True
#     )

# Merge the results
merged_df = merge_chaining_results(
    qna_dict, chatbot_dict, 
    simple_summaries_dict, relevance_dict, iteration_id, 
    empty_columns=True, pivot=True, validate=True, 
    chatbot_id=chatbot_id, save_df=True, save_chatbot=True,
    json_path=r'G:\Shared drives\content summarization\raw outputs\JSON'
    )