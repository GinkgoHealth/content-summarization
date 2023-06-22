import scrapy
from scrapy.crawler import CrawlerRunner
from crochet import setup, wait_for
import time

setup()
class spider_BMJO(scrapy.Spider):
    name = "spider_BMJO"
    
    def start_requests(self):
        urls = ['https://emails.bmj.com/q/1fnLH65XUsNn7Iiph6kELOM/wv']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_front)
    
    def parse_front(self, response):
        self.article_title = response.css('a.art-title > font::text').extract()
        article_url = response.xpath('//a[@class="art-title"]/@href').extract()
        # self.article_title = [response.css('a.art-title > font::text').extract_first()]
        # article_url = [response.xpath('//a[@class="art-title"]/@href').extract_first()]
        for index, url in enumerate(article_url):
            article_dict[index] = dict()
            article_dict[index]['journal'] = 'BMJ Open'
            article_dict[index]['title'] = self.article_title[index]
            article_dict[index]['url'] = url
            yield response.follow(url=url, callback=self.parse_pages, cb_kwargs={'index': index})
    
    def parse_pages(self, response, index):
        text = response.xpath('//h2|//p|//h3|//h4').extract()
        article_dict[index]['text'] = ''.join([line for line in text])
        
@wait_for(10)
def run_spider():
    """
    Scrape articles from non-RSS URLs. Must instantiate a blank dictionary as `article_dict` 
    before running the script.
    
    Parameters: None

    How to call the function:
    ```
    article_dict = dict()
    run_spider()

    ```
    """
    crawler = CrawlerRunner()
    d = crawler.crawl(spider_BMJO)
    return d

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







iteration_id = 1
article_dict = dict()

