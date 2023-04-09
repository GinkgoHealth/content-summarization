

def create_text_dict(text, text_dict=None):
    if text_dict == None:
        text_dict = dict()
        text_id = 1
    else:
        text_id = len(text_dict) + 1
    if type(text) == str:
    
        text_dict[text_id] = text
    elif type(text) == list:
        for value in text:
            text_dict[text_id] = value
            text_id += 1
    return text_dict