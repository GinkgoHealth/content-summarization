import scrapy
from scrapy.crawler import CrawlerRunner
from crochet import setup, wait_for
import re
from IPython import display
import time
from pprint import pprint

setup()

def trim_text(text, regex=None):
    if regex==None:
        regex = '.*<h2>Abstract</h2>.*(?:Introduction.*)?(<h2.*?>Introduction</h2>.*References)<.*' 
    try:
        processed = re.search(regex, text, re.DOTALL).group(1)
        html_display = display.HTML(processed)
    except: 
        print('Unable to parse article text')
        processed = '<Error parsing article text>' 
        html_display = processed
    return processed, html_display

def text_dict_from_web(article_dict, header=2, to_display=0,
        regex_str='.*<h\d>Abstract</h\d>.*(?:Introduction.*)?(<h\d.*?>Introduction</h\d>.*References)<.*'
        ):
    """
    Create a text dictionary from a dictionary containing web-scraped articles.

    Parameters:
        article_dict (dict): Values of each dictionary item are a dictionary representing the data from a 
            single article: 'url', 'text', and 'title'.

    Returns:
        text_dict: Dictionary where each item is a string of the text of an article, starting with the title.
    """
    journal = next(iter(article_dict.values()))['journal']
    print(f'Parsing {len(article_dict)} articles from {journal}')
    regex_str = regex_str.replace('\d', f'{header}')
    regex = rf'{regex_str}'
    print(f'Regex pattern: {regex}')
    text_dict = dict()
    display_dict = dict()
    if type(to_display) != list:
        to_display = [to_display] 
    for article_key in article_dict:
        trimmed_text, display = trim_text(article_dict[article_key]['text'], regex)
        text_dict[article_key] = f"{article_dict[article_key]['title']}\n\n{trimmed_text}"
        if article_key in to_display:
            display_dict[article_key] = display
    print(f'text_dict keys: {[key for key in text_dict.keys()]}')
    return text_dict, display_dict

class crawler_RSS1(scrapy.Spider):
    name = "crawler_RSS1"
    
    def __init__(self, n_articles):
        self.n_articles = n_articles
    
    def start_requests(self):
        journals = {
            'PLOS One': 'https://journals.plos.org/plosone/feed/atom',
            'BMJ Open': 'https://bmjopen.bmj.com/rss/current.xml',
            'Journal of Medical Internet Research': 'https://www.jmir.org/feed/atom',
            'PLOS Medicine': 'https://journals.plos.org/plosmedicine/feed/atom'

            # 'Annual Review of Medicine': 'https://www.annualreviews.org/action/showFeed?ui=45mu4&mi=3fndc3&ai=sm&jc=med&type=etoc&feed=atom' # response code 403
            }
        for index, journal in enumerate(journals):
            # article_dict[index] = dict()
            yield scrapy.Request(
                url=journals[journal], callback=self.parse_front, 
                cb_kwargs={'journal': journal, 'journal_index': index, 'article_dict': article_dict}
                )
    
    def parse_front(self, response, journal, journal_index, article_dict):
        response.selector.remove_namespaces() # This is needed for any Atom feeds
        # print('Initiation')
        try:
            if self.n_articles != 1:
                article_title = response.xpath('//entry/title/text()').getall()
                article_url = response.css('entry > link[rel="alternate"]::attr(href)').getall()
                if article_url == []:
                    print(f'\tExtracting using method 2 for {journal}')
                    article_title = response.xpath('//item/title/text()').getall()
                    article_url = response.css('item > link::text').getall()
            else:
                article_title = [response.xpath('//entry/title/text()').get()]
                article_url = [response.css('entry > link[rel="alternate"]::attr(href)').get()]
                if article_url[0] is None:
                    print(f'\tExtracting using method 2 for {journal}')
                    article_title = [response.xpath('//item/title/text()').get()]
                    article_url = [response.css('item > link::text').get()]
        except:
            print('fail')
        print(f'Found {len(article_title)} articles and {len(article_url)} URLs for {journal}')

        # This is required for BMJ Open, which for some reason repeats each article title.
        if len(article_title) == len(article_url) * 2:
            unique_article_title = []
            [unique_article_title.append(article) for article in article_title if article not in unique_article_title]
            article_title = unique_article_title
            print(f'\tCorrected number of article titles: {len(article_title)}')
        if type(n_articles) == int:
            article_url = article_url[:n_articles]

        for index, url in enumerate(article_url):
            # print(url)
            key = round(journal_index + index/100, 2)
            article_dict[key] = {
                'journal': journal,
                'title': article_title[index],
                'url': url
            }
            yield response.follow(
                url=url, callback=self.parse_pages, 
                cb_kwargs={'key': key, 'article_dict': article_dict})
                
    
    def parse_pages(self, response, key, article_dict):
        # print(f'Journal #{key}')
        text = response.xpath('//h2|//p|//h3|//h4').extract()
        article_dict[key]['text'] = ''.join(['\n'+line for line in text])
        if key - int(key) == 0:
            print(f'\t{article_dict[key]["journal"]}')
            print(f'\t\tArticle attributes: {[key for key in article_dict[key].keys()]}')
        
@wait_for(40)
def run_RSS_spider(n_articles='all'):
    """
    Scrape articles from RSS feeds. Must instantiate a blank dictionary as `article_dict` before running the script.
    Parameters:
        - n_articles (int): Number of articles to scrape from each journal. 
            If 'all' or other non-integer value, scrape all articles. Default is 'all'.

    How to call the function:
    ```
    article_dict = dict()
    run_RSS_spider(n_articles)

    ```
    """
    crawler = CrawlerRunner()
    d = crawler.crawl(crawler_RSS1, n_articles)
    return d

def article_titles(article_dict):
    """
    Print the titles of the articles in a dictionary of articles.
    """
    for article in sorted(article_dict):
        print(f"{article}: {article_dict[article]['title']}")
        print(f"\t{article_dict[article]['journal']} {article_dict[article]['url']}\n")

def save_article_dict(article_dict, path, description='scraped_articles_dict', append_version=True,
    save_pickle=True, save_json=False, to_csv=False):
    """
    Save a dictionary of articles to a file. Default behaviour is to save as a pickle only.
    Parameters:
        - article_dict (dict): Dictionary of articles.
        - path (str): Path to save the file.
        - description (str): Description of the file for the filename.
        - append_version (bool): If True, append the date to the filename.
        - save_pickle (bool): If True, save the dictionary as a pickle file.
        - save_json (bool): If True, save the dictionary as a JSON file.
        - to_csv (bool): If True, convert the dictionary to a DataFrame to save as a CSV file.
    """
    if save_pickle == True:
        savepickle(article_dict, filename=f'{description}_', path=path, append_version=append_version)
    if save_json == True:
        save_to_json(article_dict, description=description, path=path, append_version=append_version)
    if to_csv == True:
        save_csv(pd.DataFrame(article_dict).transpose(), path=path, filename=f'{description}_',
            index=False, append_version=append_version)


iteration_id = 2.82
# main_dict = dict()
article_dict = dict()
n_articles = 2
run_RSS_spider(n_articles)

main_dict[iteration_id] = article_dict
# sorted(article_dict.keys())

# save_article_dict(article_dict, path='../web_articles/2023-06-21', to_csv=True, save_json=True)
article_titles(article_dict)

# time.sleep(10)
# text_dict, display_dict = text_dict_from_web(article_dict, to_display=[0])







iteration_id = 1
article_dict = dict()

