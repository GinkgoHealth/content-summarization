import requests
import pandas as pd
import json
import re
import os
import string
api_key = os.getenv('api_ncbi')


def search_article(title, api_key, verbose=False):
    """
    Search for article title in PubMed database.

    Parameters:
    - title (str): article title
    - api_key (str): NCBI API key

    Returns:
    response (str): Article metadata from PubMed database if present. Otherwise, returns list of PMIDs.
    """
    base_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    title_without_not = re.sub(r'not', '', title)
    if api_key:
        base_url += f'&api_key={api_key}'
    params = {
        'db': 'pubmed',
        'term': title_without_not,
        'field': 'title',
        'retmax': 5,
        'retmode': 'json'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    cleaned_title = re.sub(f'[{string.punctuation}]', '', title).lower().strip()

    try:
        id_list = data['esearchresult']['idlist']
        if id_list:
            result = retrieve_citation(id_list[0], api_key).decode('utf-8')
            cleaned_result = re.sub(f'[{string.punctuation}]', '', result).lower().strip()
            for article_id in id_list:
                result = retrieve_citation(article_id, api_key).decode('utf-8')
                if cleaned_title in cleaned_result:
                    if verbose:
                        print(f'Match found for {title}: PMID = {article_id}.')
                    return result
            print('Article title not found in PMIDs.')
            print(f'\tInput title: {title.lower().strip()}')
            # print(f'Result title: {re.sub(r":", r"", result.lower())}')
            return id_list        
    except:
        print('Article not found.')
        return id_list 
    
def retrieve_citation(article_id, api_key):
    """
    Retrieve article metadata from PubMed database.
    """
    base_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    if api_key:
        base_url += f'&api_key={api_key}'
    params = {
        'db': 'pubmed',
        'id': article_id
    }

    response = requests.get(base_url, params=params)
    return response.content

def extract_pubmed_details(record_string):
    """
    Helper function called by `pubmed_details_by_title` to parse article metadata from PubMed database.
    """
    authors = re.findall(r'<Author ValidYN="Y".*?><LastName>(.*?)</LastName><ForeName>(.*?)</ForeName>', record_string)
    formatted_authors = ', '.join(['{} {}'.format(author[1], author[0]) for author in authors])

    # Extract publication year
    publication_year = re.search(r'<PubDate><Year>(\d{4})</Year>', record_string)
    publication_year = publication_year.group(1) if publication_year else ''
    publication_month = re.search(r'<PubDate>.*?<Month>(Aug)</Month>.*?</PubDate>', record_string)
    publication_month = publication_month.group(1) if publication_month else ''

    # Extract article title
    article_title = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', record_string)
    article_title = article_title.group(1) if article_title else ''

    # Extract journal title
    journal_title = re.search(r'<Title>(.*?)</Title>', record_string)
    journal_title = journal_title.group(1) if journal_title else ''

    # Extract journal volume
    journal_volume = re.search(r'<Volume>(.*?)</Volume>', record_string)
    journal_volume = journal_volume.group(1) if journal_volume else ''

    # Extract journal issue
    journal_issue = re.search(r'<Issue>(.*?)</Issue>', record_string)
    journal_issue = journal_issue.group(1) if journal_issue else ''

    # Extract start page
    start_page = re.search(r'<StartPage>(.*?)</StartPage>', record_string)
    start_page = start_page.group(1) if start_page else ''

    # Extract end page
    end_page = re.search(r'<EndPage>(.*?)</EndPage>', record_string)
    end_page = end_page.group(1) if end_page else ''

    # Extract ELocationID
    doi = re.search(r'<ELocationID.*?EIdType="doi".*?>(.*?)</ELocationID>', record_string)
    doi = doi.group(1) if doi else ''

    abstract = re.search(r'<AbstractText.*?>(.*?)</AbstractText>', record_string)
    abstract = abstract.group(1) if abstract else ''

    return {
        'pubmed_title': article_title,
        'abstract': abstract,
        'publication': journal_title,
        'authors': formatted_authors,
        'year': publication_year,
        'month': publication_month,
        'pub_volume': journal_volume,
        'pub_issue': journal_issue,
        'start_page': start_page,
        'end_page': end_page,
        'doi': doi,
    }


def pubmed_details_by_title(title, api_key):
    """
    Search for article title in PubMed database and return article details.

    Parameters:
    - title (str): article title
    - api_key (str): NCBI API key

    Returns:
    article_details (dict): Article metadata from PubMed database if present. Otherwise, returns list of PMIDs.
    """
    record_string = search_article(title, api_key)
    # return record_string
    if len(record_string) > 0:
        article_details = extract_pubmed_details(record_string)
        return article_details
    else:
        return None

def add_pubmed_details(text_df, api_key):
    """
    Add the article metadata to a DataFrame containing article title and text.

    Parameters:
    - text_df (pd.DataFrame): DataFrame containing article title and text.
    - api_key (str): NCBI API key

    Returns:
    DataFrame with added PubMed details for each article.
    """
    article_details_list = []
    for article in text_df['title']:
        article_details = pubmed_details_by_title(article, api_key)
        if article_details:
            article_details_list.append(article_details)
        else:
            article_details_list.append({
                'pubmed_title': article,
                'abstract': '',
                'publication': '',
                'authors': '',
                'year': 0,
                'month': '',
                'pub_volume': '',
                'pub_issue': '',
                'start_page': '',
                'end_page': '',
                'doi': '',
            })
    article_details_df = pd.DataFrame(article_details_list)
    return pd.concat([text_df.reset_index(drop=True), article_details_df], axis=1)

def compare_columns(df, col1='title', col2='pubmed_title'):
    """
    Compare two columns in a DataFrame. Drop the second column if the two columns are identical.
    Otherwise, return the dataframe with new column with the comparison results, 
    where `True` indicates a mismatch.

    Parameters:
    - df (pd.DataFrame): DataFrame containing the two columns to be compared.
    - col1 (str): Name of the first column to be compared.
    - col2 (str): Name of the second column to be compared.

    Returns:
    DataFrame with added column containing the comparison results.
    """
    # Remove punctuation and special characters
    remove_punct = lambda text: re.sub(f'[{string.punctuation}]', '', text)
    col1 = df[col1].apply(remove_punct)
    col2 = df[col2].apply(remove_punct)

    # Convert to lowercase and remove white spaces
    clean_text = lambda text: text.lower().strip()
    col1 = col1.apply(clean_text)
    col2 = col2.apply(clean_text)

    # Perform the comparison
    comparison = col1 != col2
    if sum(comparison) == 0:
        df = df.drop(columns=['pubmed_title'])
    else:
        df['flag_title'] = comparison
    
    return df