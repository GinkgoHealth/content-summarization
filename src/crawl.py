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









iteration_id = 1
article_dict = dict()

