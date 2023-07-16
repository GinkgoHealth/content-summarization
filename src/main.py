
from functools import wraps
import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\private")
import prompts
from db_orm import *

text_df = get_table(table='gpt_queue')
print(text_df)