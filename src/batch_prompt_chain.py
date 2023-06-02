import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
from summary_chain import *
from response_processing import *
from article_processing import create_text_dict_from_folder
from file_functions import *
import time

# Create text dictionary
folder_path = '../text/2023-06-02 1' # ** UPDATE REQUIRED**

encoding='ISO-8859-1'
subset=None

text_dict = create_text_dict_from_folder(folder_path, encoding=encoding, subset=subset)

# Set parameters
iteration_id = 1
n_choices = 5
pause_per_request=0
summary_iteration_id = iteration_id
chatbot_id = iteration_id

# Create prompt lists
prep_step = [
    "Take the key points and numerical descriptors to",
]

summarize_task = [
    "Summarize for a LinkedIn post.",
    # "Describe the interesting points to your coworker at the water cooler",
    # "Create an Instagram post without hashtags.",
]

user_simplify_task = [
    """If needed, rewrite the text using terms appropriate for the audience. If not keep it the same.\
    Follow these steps to accomplish this: \
    \n1. Check if the content and language are appropriate for the audience. \
    \n2. If it is suitable for the audience, keep it the same. If not, rewrite using terms appropriate for the audience. \ 
    \n3. Return the final version of the summary to be shown to the audience. \
    \n\nYour audience is""",
]

simplify_audience = [
    # "a lay audience",
    "people without a science background",
]

user_relevance_task = [
    """Rewrite this summary to include a statement of how it is relevant for the audience. \
        Follow these steps to accomplish this: \
        \n1. Think about why this might be relevant for the audience in the grand scheme of things.\
        \n2. If it is not evident why the text is relevant for the audience in the grand scheme of things, \
        add a sentence to inform the audience. Otherwise, keep it the same. \
        \n3. Modify the summary if needed to reduce redundancy. \
        \n4. Check if the content and language are appropriate for the audience. \
        If it is suitable for the audience, keep it the same. If not, rewrite using terms appropriate for the audience. \ 
        \n5. Return the final version of the summary to be shown to the audience. \
        \n6. Remove the backticks.
        \n\nYour audience consists of""",
]

relevance_audience = [
    # "seniors",
    "people who enjoy sports",
    "people new to resistance training"
]

qna_dict = dict()
chatbot_dict = dict()
simple_summaries_dict = dict()
relevance_dict = dict()
chain_results_dict = dict()

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

# Add relevance
relevance_prompts = user_relevance_task
relevance = prompt_chaining_dict(relevance_prompts, relevance_audience, relevance_dict, 
    chaining_dict[summary_iteration_id], iteration_id, prompt_column='relevance', 
    n_choices=1, pause_per_request=pause_per_request, summary_iteration_id=summary_iteration_id
    )

# Merge the results
try:
    chain_results_dict = merge_all_chaining_results(
        chain_results_dict, chatbot_dict, iteration_id, pivot=True,
        empty_columns=True,
        save_df=True, save_chatbot=True, 
            csv_path=folder_path,
    )
    print(f'\nCompleted merge_all_chaining_results!:)')
except:
    merged_df = merge_chaining_results(
        qna_dict, chatbot_dict, 
        simple_summaries_dict, relevance_dict, iteration_id, 
        empty_columns=True, pivot=True, validate=True, 
        chatbot_id=chatbot_id, save_df=True, save_chatbot=True,
        csv_path=folder_path, pickle_path=folder_path, json_path=folder_path
        )
    print(f'\nCompleted merge_chaining_results.')