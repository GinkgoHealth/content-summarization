
from functools import wraps
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\private")
import prompts
from db_orm import *
from sources import *

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
text_df = get_table(table='gpt_queue')
references_df_dict[iteration_id] = create_sources_table(text_df, section=None)
print(references_df_dict[iteration_id])
print(prompts.api_key_pubmed)
print(prompts.api_key)