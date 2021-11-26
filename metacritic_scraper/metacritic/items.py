# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MetacriticItem(scrapy.Item):
    # Game information
    appname = scrapy.Field()
    rating = scrapy.Field() #esrb rating
    num_of_players = scrapy.Field() # # of players

    pass

class UserReveiwItem(scrapy.Item):
    # Users' reviews
    appname = scrapy.Field()
    user_name = scrapy.Field()
    date = scrapy.Field()
    rating_score = scrapy.Field()
    review = scrapy.Field()
    page = scrapy.Field()
    pass

class UserInfoItem(scrapy.Item):
    # User information
    user_name = scrapy.Field()
    review_product = scrapy.Field() # game that user reviewed
    date = scrapy.Field()
    average_user_score = scrapy.Field()
    rating_score =  scrapy.Field() 
    
    pass 
