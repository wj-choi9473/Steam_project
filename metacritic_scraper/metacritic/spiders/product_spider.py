# MetacriticItem
import pandas as pd # For load 
import numpy as np
import scrapy
import requests
from metacritic.items import MetacriticItem


def make_url_name(name):
    """
    return url format name
    """
    name = str(name)
    name = name.replace(" ", "-")
    name = name.replace(":", "")
    name = name.replace("'", "")
    name = name.replace("&amp;", "and")
    name = name.replace(",", "")
    name = name.replace(".", "")
    return name.lower()


class MetacriticSpider(scrapy.Spider):
    name = "metacritic_products"
    allow_domain = ["https://www.metacritic.com"]
    # use fake useragent 
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 300,
        }
    }

    def start_requests(self): 
        appnames = pd.read_pickle("../../../../steam_project/data/crawled_data/applist.pickle")["appname"].apply(make_url_name)
        urls = [f"https://www.metacritic.com/game/pc/{appname}" for appname in appnames]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self,response):
        
        # Load data
        item = MetacriticItem()
        
        item["appname"] = response.xpath('//*[@class="product_title"]/a/h1/text()').extract_first()

        try:
            item["rating"] = response.xpath('//*[@class="summary_detail product_rating"]/span/text()').extract()[1] # esrb rating
        except: 
            item["rating"] = np.nan
        try:
            item["num_of_players"] = response.xpath('//*[@class="summary_detail product_players"]/span/text()').extract()[1] # number of game players in game
        except:
            item["num_of_players"] = np.nan
        yield item






