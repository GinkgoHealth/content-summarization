from functools import wraps
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\private")
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
from prompts import * # .py file stored in the path above
from db_orm import * 
from sources import *
from orm_summarize import *
from article_processing import *

#########
#########
# Prep: Set parameters
folder_path = '../text/2023-07-14 full'
section = 'discussion'
local = False
n_choices = 1
article_limit = 4
temperature = 1
pause_per_request=0
# summary_iteration_id = iteration_id
iteration_id = 1
chatbot_id = iteration_id
model = 'gpt-3.5-turbo-16k-0613'
# model = 'gpt-4'
save_outputs=False

def generate_summaries(n_choices, temperature, model, pause_per_request, folder_path, section, local, queue_id=queue_id, article_limit=article_limit):
    ### Set up
    qna_dict = dict()
    chatbot_dict = dict()
    references_df_dict = dict()

    # set the option to wrap text within cells
    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.max_rows', 20)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    ####### 
    # Step 1: Create sources table
    if local:
        text_df = parse_fulltext(folder_path, section).iloc[:article_limit if article_limit else len(text_df)]
    elif queue_id:
        if (type(queue_id) == list) & (len(queue_id) > 1):
            print('Converting queue_id list to tuple')
            queue_id = tuple(queue_id)
        elif (type(queue_id) == list):
            print('Converting queue_id list to number')
            queue_id = queue_id[0]
        if type(queue_id) == tuple:
            text_df = get_table(
                table='gpt_queue', limit=article_limit, 
                filter_statement=f'id IN {queue_id}'
                )
        else:
            text_df = get_table(
                table='gpt_queue', limit=article_limit, 
                filter_statement=f'id = {queue_id}'
                )
    else:
        text_df = get_table(table='gpt_queue', limit=article_limit, order='DESC') # db_orm.py
    references_df_dict[iteration_id] = create_sources_table(text_df) # sources.py

    ###### 
    # Step 2:  Add rows from gpt_queue table to sources table 
    bulk_append(table='sources', input_df=references_df_dict[iteration_id]) # db_orm.py

    # ##### 
    # Step 3: Get the new sources for summarization
    sources_df = get_from_queue(input_df=text_df, order_by='id', order='ASC')

    # ##### 
    # Step 4: Create summaries (functions contained in orm_summarize.py)
    chatbot_dict = batch_summarize( # orm_summarize.py
        sources_df, folder_path, prep_step, summarize_task, edit_task,  # parameter values found in prompts.py
        simplify_task, simplify_audience, format_task,
        chatbot_dict, temperature=temperature,
        system_role=system_role, model=model, max_tokens=1000,
        n_choices=n_choices, pause_per_request=pause_per_request,
        iteration_id=iteration_id, save_outputs=save_outputs
        )
    #########
    # Step 5: Create summaries table
    qna_dict = create_summaries_df(
        qna_dict, chatbot_dict, iteration_id, chatbot_id=chatbot_id
        )

    ##########
    # Step 5: Add results to summaries and prompts table 
    bulk_append(table='summaries', input_df=qna_dict[iteration_id]) # db_orm.py

    return qna_dict[iteration_id]

if __name__ == "__main__":
    qna_dict = generate_summaries(n_choices, temperature, model, pause_per_request, folder_path, section, local=local, article_limit=article_limit)
    print(qna_dict[iteration_id])