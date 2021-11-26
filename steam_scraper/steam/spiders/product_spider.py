import pandas as pd # For load 
import re
import scrapy
from scrapy.http import FormRequest

import requests
import logging

from steam.items import SteamItem

logger = logging.getLogger(__name__)

class SteamSpider(scrapy.Spider):
    name = "steam_products"

    def start_requests(self): 
        appids = pd.read_pickle("../../../../data/crawled_data/applist.pickle")["appid"]
        urls = [f"https://store.steampowered.com/app/{appid}/" for appid in appids]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self,response):
        # Circumvent age selection form.
        if '/agecheck/app' in response.url:
            logger.debug(f'Form-type age check triggered for {response.url}.')

            form = response.css('#agegate_box form')

            action = form.xpath('@action').extract_first()
            name = form.xpath('input/@name').extract_first()
            value = form.xpath('input/@value').extract_first()

            formdata = {
                name: value,
                'ageDay': '7',
                'ageMonth': '3',
                'ageYear': '1994'
            }

            yield FormRequest(
                url=action,
                method='POST',
                formdata=formdata,
                callback=self.parse
            )
        else:
            # Load data
            item = SteamItem()
        
            item["appid"] = str(response.url).split("/")[4] # Unique numbers for each games
            item["genres"] = response.xpath('//*[@id="genresAndManufacturer"]/a/text()').extract() 
            item["title"] = response.xpath('//*[@id="appHubAppName"]/text()').extract()[0] # Game product name 
            item["developer"] = response.xpath('//*[@id="developers_list"]/a/text()').extract()[0]
            item["publisher"] = response.xpath('//*[@id="game_highlights"]/div[1]/div/div[3]/div[4]/div[2]/a/text()').extract()[0]
            item["release_date"] = response.xpath('//*[@id="game_highlights"]/div[1]/div/div[3]/div[2]/div[2]/text()').extract()[0]

            user_tags = response.xpath('//*[@id="glanceCtnResponsiveRight"]/div[2]/div[2]/a/text()').extract()
            user_tags = [tag.replace("\r\n\t","").replace("\t","") for tag in user_tags]
            item["user_tags"] = user_tags # Popular user-defined tags for this product

            item["specs"] = response.xpath('//*[@id="category_block"]/div/a/text()').extract() # Additional infos 

            sysreq = str(response.css(".bb_ul").extract())
            sysreq = re.sub('<[^<]+?>', '@', sysreq).replace("@@@@","#").replace("[","").replace("]","").replace("'","").split('#')
            sysreq = [req.replace("@","") for req in sysreq]
            item["sys_requirement"] = sysreq # system requirements to play game

    
            yield item

                
            



