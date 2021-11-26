# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SteamItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    appid = scrapy.Field()
    user_tags = scrapy.Field()
    specs = scrapy.Field() 
    title = scrapy.Field() 
    genres = scrapy.Field()
    developer = scrapy.Field()
    publisher = scrapy.Field()
    release_date = scrapy.Field()
    sys_requirement = scrapy.Field()

    pass
