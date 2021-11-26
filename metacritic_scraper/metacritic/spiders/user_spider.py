import pandas as pd 
import scrapy
from metacritic.items import UserInfoItem


class MetacriticSpider(scrapy.Spider):
    name = "metacritic_userinfo"
    allow_domain = ["https://www.metacritic.com/"]
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 300,
        }
    }
    def start_requests(self): 
        usernames = pd.read_pickle("../../../../steam_project/data/crawled_data/metacritic_user_reviews.pickle")["user_name"].unique()
        urls = [f"https://www.metacritic.com/user/{username}?myscore-filter=Game&myreview-sort=date&page=0" for username in usernames]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.page_parse)
    
    def page_parse(self, response):
        item = UserInfoItem()
        # User information

        item["user_name"] = response.xpath('//*[@class="name"]/text()').extract_first()
        item["review_product"] = response.xpath('//*[@class="product_title"]/a/text()').extract()[2:]
        item["date"] = response.xpath('//*[@class="date"]/text()').extract()
        item["average_user_score"] = response.xpath('//*[@class="product_score"]/span[2]/text()').extract()
        item["rating_score"] = response.xpath('//*[@class="review_score"]/div/text()').extract()
        yield item

        next_page = response.xpath('//*[@class="flipper next"]/a/@href').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(url=next_page, callback=self.page_parse)

                
            



