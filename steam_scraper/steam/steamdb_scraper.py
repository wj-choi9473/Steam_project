import time
import datetime
import random
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

"""
This dataset is aquired from SteamDB. 
SteamDB does not allow scraping/crawling except for educational purpose.
You must contact them and get permission before scraping/crawling the data.

This scraper collects game lists on steam, price history,
number of game players and twitch viewers history on game-level.
"""
# only for educational purpose, set user agent
useragent = "SteamDB-Educational-Access;"

def appchart_scrape() -> pd.DataFrame:
    """
    Scrape game rank chart on SteamDB: game's id, game name, current number of player, all-time
    """
    url = "https://steamdb.info/graph/"
    headers = {"user-agent": useragent}

    response = requests.get(url, headers=headers)
    doc = BeautifulSoup(response.content, "html.parser")
    elements = doc.select(".app")

    applist = []
    for element in elements:
        applist.append(
            {
                "appid": element.get("data-appid"),
                "appname": element.select_one("td:nth-of-type(4) > a").text,
                "alltimepick": element.select_one("td:nth-of-type(7)").text.replace(",",""),
                "current": element.select_one("td:nth-of-type(5)").text.replace(",",""),
            }
        )

    applist_df = pd.DataFrame(applist)
    applist_df = applist_df[1:].reset_index().drop(columns=["index"])
    
    return applist_df

def price_scrape(applist_df):
    """
    Scrape price and sales history of games
    applist_df: applist DataFrame from appchart_scrape
    """
    appids = applist_df["appid"]
    price_info_df = pd.DataFrame()
    headers = {"user-agent": useragent}

    for appid in tqdm(appids):
        url = f"https://steamdb.info/api/GetPriceHistory/?appid={appid}&cc=us"

        response = requests.get(url, headers=headers)
        pricedata = response.json()
        pricedata_df = pd.DataFrame(pricedata["data"]["history"]).rename(columns={
            'x' : 'time',
            'y' : 'price',
            'f' : 'price_us',
            'd' : 'discount_rate'
        })
        try:
            pricedata_df["time"] = pricedata_df["time"].apply(lambda x : str(x)[:-3])
            pricedata_df["time"] = pricedata_df["time"].apply(convert_datetime)
        except:
            pricedata_df["time"] = 1
        
        try:
            pricedata_df["price"] = pricedata_df["price"].astype(float)
        except:
            pricedata_df["price"] = 0
        
        try:
            pricedata_df["price_us"] = pricedata_df["price_us"].apply(lambda x : x.replace("$","$ "))
        except:
            pricedata_df["price_us"] = 0
            
        try:
            pricedata_df["discount_rate"] = pricedata_df["discount_rate"].astype(float)
        except:
            pricedata_df["discount_rate"] = 0
            
        pricedata_df["appid"] = appid


        sales_df = pd.DataFrame.from_dict(pricedata["data"]["sales"], orient="index")
        try:
            sales_df = sales_df.reset_index().rename(columns={'index':'time',0:'discount_name'})
            sales_df["time"] = sales_df["time"].apply(lambda x : str(x)[:-3])
            sales_df["time"] = sales_df["time"].apply(convert_datetime)
        except:
            sales_df["time"] = np.nan
        
        try:
            sales_df["discount_name"] = sales_df["discount_name"].astype(str)
        except:
            sales_df["discount_name"] = np.nan
            
        sales_df["appid"] = appid
        
        df = pd.merge(pricedata_df, sales_df, how="outer", on=['time','appid'])
        price_info_df = pd.concat([price_info_df, df], axis=0)

    return price_info_df

def appdemand_scrape(applist_df,time_freq="D"):
    """
    Scrape number of players and twitch viwers history

    applist_df: df from appchart_scrape()
    time_freq: str or DateOffset. "D" for daily "W" for weekly history, default "D".
    """
    appids = applist_df["appid"]
    appdemand_df = pd.DataFrame()
    headers = {"user-agent": useragent}

    if time_freq == "D":
        api_option = "max"
    elif time_freq == "W":
        api_option = "week"
    
    for appid in tqdm(appids):
        url = f"https://steamdb.info/api/GetGraph/?type=concurrent_{api_option}&appid={appid}"
        response = requests.get(url, headers=headers)
        data = response.json()
        if data["success"] == True:
            try:
                start_twitch = convert_datetime(data["data"]["start_twitch"])   
                values_twitch = data["data"]["values_twitch"]
            except:
                start_twitch = np.nan
                values_twitch = np.nan

            start = convert_datetime(data["data"]["start"])
            values = data["data"]["values"]

            play_df = pd.DataFrame({
                "appid" : appid,
                "time" : pd.date_range(start=start, periods=len(values), freq=time_freq),
                "value" : values
            })

            try:
                twitch_df = pd.DataFrame({
                    "appid" : appid,
                    "time" : pd.date_range(start=start_twitch, periods=len(values_twitch), freq=time_freq),
                    "values_twitch" : values_twitch

                })
            except:
                twitch_df = pd.DataFrame({
                    "appid" : appid,
                    "time" : pd.date_range(start=start, periods=len(values), freq=time_freq),
                    "values_twitch" : values_twitch

                })
            demand_df = pd.merge(play_df,twitch_df,how= 'outer', on = ['appid','time'])

            appdemand_df = pd.concat([appdemand_df,demand_df], axis = 0)
        else:
            pass
    return appdemand_df

def convert_datetime(unixtime):
    """Convert unixtime to datetime"""
    unixtime = int(unixtime)
    date = datetime.datetime.fromtimestamp(unixtime).strftime("%Y-%m-%d")
    return date  


if __name__ == "__main__":
    applist_df = appchart_scrape()
    applist_df.to_pickle("../data/crawled_data/applist.pickle")

    price_sale_df = price_scrape(applist_df)
    price_sale_df.to_pickle("../data/crawled_data/price_sale.pickle")
    
    appdemand_df = appdemand_scrape(applist_df,time_freq="D")
    appdemand_df.to_pickle("../data/crawled_data/appdemand.pickle")

    appdemand_week_df = appdemand_scrape(applist_df,time_freq="W")
    appdemand_week_df.to_pickle("../data/crawled_data/appdemand_week.pickle")