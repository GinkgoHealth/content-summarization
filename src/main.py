
from functools import wraps
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\private")
from prompts import * # .py file stored in the path above
from db_orm import *
from sources import *
from orm_summarize import *

#########
# Prep: Set parameters
iteration_id = 1
temperature = 1
n_choices = 2
pause_per_request=10
# summary_iteration_id = iteration_id
chatbot_id = iteration_id
model = 'gpt-3.5-turbo-16k-0613'
# model = 'gpt-4'
save_outputs=True
folder_path = '/database'

def generate_summaries(n_choices, temperature, model, pause_per_request, folder_path):
    ### Set up
    qna_dict = dict()
    chatbot_dict = dict()
    references_df_dict = dict()

    # set the option to wrap text within cells
    pd.set_option('display.max_colwidth', 100)
    pd.set_option('display.max_rows', 20)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    ####### 
    # Step 1: Create sources table
    text_df = get_table(table='gpt_queue') # db_orm.py
    references_df_dict[iteration_id] = create_sources_table(text_df, section=None) # sources.py

    ###### 
    # Step 2:  Add rows from gpt_queue table to sources table IF NOT ALREADY ADDED
    bulk_append(table='sources', input_df=references_df_dict[iteration_id]) # db_orm.py

    # ##### 
    # Step 3: Get the new sources for summarization
    article_limit = len(references_df_dict[iteration_id])
    sources_df = get_table(table='sources', limit=article_limit, order='DESC') # db_orm.py

    # ##### 
    # Step 3: Create summaries (functions contained in orm_summarize.py)
    chatbot_dict = batch_summarize( # orm_summarize.py
        sources_df, folder_path, prep_step, summarize_task, edit_task,  # parameter values found in prompts.py
        simplify_task, simplify_audience, format_task,
        chatbot_dict, temperature=temperature,
        system_role=system_role, model=model, max_tokens=1000,
        n_choices=n_choices, pause_per_request=pause_per_request,
        iteration_id=iteration_id, save_outputs=save_outputs
        )
    #########
    # Step 4: Create summaries table
    qna_dict = create_summaries_df(
        qna_dict, chatbot_dict, iteration_id, chatbot_id=chatbot_id
        )

    ##########
    # Step 5: Add results to summaries and prompts table 
    bulk_append(table='summaries', input_df=qna_dict[iteration_id]) # db_orm.py

    return qna_dict[iteration_id]