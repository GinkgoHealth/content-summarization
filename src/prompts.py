system_role = "You are someone who loves to read health research and tell your friends about it."
# system_role = "You are an expert at science communication."

summarize_task = [
    # f"1. Describe the interesting points of the research to your coworker.",
    # "1. Summarize for an instagram post.",
    # "1. Tell your friend about the research in a text message.",
    "Write a casual text message to your friend about the research.",
    # "Describe the interesting points to your coworker at the water cooler.",
    # "Take the key points and numerical descriptors to",
]
prep_step = [
    # "Tell your friend about the research in a text message.",

    "In the summary, cover the following information: \
    \n- Identify the key points and statistics from this text that would make interesting or helpful health content. \
    \n- If available, include the effect sizes found in the research. \
    Otherwise, skip this step. \
    \n- If applicable, get a brief description of the research participants, \
    such as age, sex, and health conditions. Otherwise, you can skip this step.\
    \n- Think about why the general population should care about the research.",

    "In the summary, cover the following information: \
    \n- Identify the key points and statistics from this text that would make interesting or helpful health content. \
    \n- If available, include the effect sizes found in the research. \
    Otherwise, skip this step. \
    \n- If applicable, get a brief description of the research participants, \
    such as age, sex, and health conditions. Otherwise, you can skip this step.\
    \n- Think about why the your friend should care about the research.",

    # "In the summary, cover the following information: \
    # \n- Identify the key points and numerical descriptors from this text that would make interesting or helpful health content. \
    # \n- If available, include the effect sizes found in the research. \
    # Otherwise, skip this step. \
    # \n- If applicable, get a brief description of the research participants, \
    # such as age, sex, and health conditions. Otherwise, you can skip this step.\
    # \n- Think about why the general population should care about the research.",
    # "In the summary, cover the following information: \
    # \n- Identify the key points and statistics from this text that would make interesting or helpful health content. \
    # \n- If available, include the effect sizes found in the research. \
    # Otherwise, skip this step. \
    # \n- If applicable, get a brief description of the research participants, \
    # such as age, sex, and health conditions. Otherwise, you can skip this step.\
    # \n- Think about why the your friend should care about the research.",

    # "Take the key points and numerical descriptors to",
    
    # "Describe the interesting points to your coworker at the water cooler."
]

edit_task = [
    """
    Once you have written your text message: \
    \nEvaluate your text message to see if it may be confusing or redundant. \
    \nIf so, re-write it so it is clear and concise. Otherwise, keep it the same. \
    \n2. Create an intriguing subject line for the text.
    """,

    # ""
]

simplify_task = [
    # """3. If needed, rewrite the text using terms appropriate for the audience. If not keep it the same.\
    # Follow these steps to accomplish this: \
    # \na. Check if the content and language are appropriate for the audience. \
    # \nb. If it is suitable for the audience, keep it the same. \
    # If not, rewrite using terms appropriate for the audience while keeping the news-worthy details. \ 
    # \nc. Return the final version of the summary to be shown to the audience. \
    # \n\nYour audience is""",

    """3. Rewrite the text in a fun tone.\
    Follow these steps to accomplish this: \
    \na. Check if the content and language are appropriate for the audience. \
    \nb. If it is suitable for the audience, keep it the same. \
    If not, rewrite using terms appropriate for the audience. \
    \nc. Check that the rewritten text is accurate. If not, correct it. \ 
    \nc. Return the final version of the summary to be shown to the audience. \
    \n\nYour audience is""",

    """3. Make a more concise and simple version of the summary.\
    Follow these steps to accomplish this: \
    \a. Rewrite it to have only the most interesting finding. \
    \nb. Check if the content and language are appropriate for the audience. \
    \n. If it is suitable for the audience, keep it the same. \
    If not, rewrite using terms appropriate for the audience. \
    \nc. Check that the rewritten text is accurate. If not, correct it. \ 
    \nd. Return the final version of the summary to be shown to the audience. \
    \n\nYour audience is""",

    # ""
]

simplify_audience = [
    "people who like fun facts but don't know much science",
    # "a lay audience",
    # ""
]

format_task = [
    """4. Return your final response in a JSON format with the following format: \
    \n{"headline": <subject line from step 2>, \
    \n"body": <text from step 1>,
    \n"audience": <rewritten text from step 3>}""",

    
    # """4. Return your final response in a JSON format with the following format: \
    # \n{"headline": <subject line from step 2>, \
    # \n"body": <text from step 1>,
    # \n"audience": "None"}""",

    
    # """4. Return your final response in a JSON format with the following format: \
    # \n{"headline": "None", \
    # \n"body": <text from step 1>,
    # \n"audience": "None"}"""
]
