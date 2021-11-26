import pandas as pd
from selenium import webdriver
import pyautogui
import clipboard
import time
from tqdm import tqdm
import random

"""
This dataset is aquired from SteamDB. 
SteamDB does not allow scraping/crawling except for educational purpose.
You must contact them and get permission before scraping/crawling the data.

This scraper collects update history of each game on Steam.
I used selenium and pyautogui to scrape data because bots are restricted. 
Be aware that SteamdDB have daily limit to access.
"""

def split_list(ls, n):
    """
    split list,df into n elements
    """
    for i in range(0, len(ls), n): 
        yield ls[i:i + n] 

def load_split_applist(n=100):
    """
    Load list of game appids and break a list into chunks of size n
    n: size N to chunk, defalut = 100
    """
    appids = pd.read_pickle("/Users/wonjae/Google Drive/steam_project/data/crawled_data/applist.pickle")["appid"]
    appids_ls = list(split_list(appids, n))
    return appids_ls

def check_message(coordinates, duration=1, button='left')-> str:
    """
    Check whether you are banned from website
    It is simply drag what you want -> save it to clipboard -> return as string
    coordinates: 2 sets(list,tuple) of x,y coordinates from start to end for draging e.g. (2692, -342),(2837, -342)
    """
    clipboard.copy("reset")
    pyautogui.moveTo(coordinates[0])  # change coordinates based on monitor size
    pyautogui.dragTo(coordinates[1] ,duration=duration, button=button)
    time.sleep(0.51)
    pyautogui.hotkey('command', 'c')
    time.sleep(0.51)
    check = clipboard.paste()
    return check

def scrape_update(start, appid):
    # drag
    pyautogui.moveTo(start)
    pyautogui.dragTo(3757, -50, duration=1, button='left')
    time.sleep(2)
    # load to clipboard
    pyautogui.hotkey('command', 'c')
    # to df
    update_history = pd.read_clipboard(sep='\\t')
    update_history["appid"] = appid
    return update_history





if __name__ == "__main__":

    
    appids_ls = load_split_applist()
    driver = webdriver.Chrome()
    update_history_df = pd.DataFrame()

    for appids in appids_ls:

        for appid in tqdm(appids):
            url = f"https://steamdb.info/app/{appid}/patchnotes/"
            driver.get(url)
            
            ban = (3222, -729),(3319, -728) # Coordinates to check temporarly banned
            updatetable = (2692, -342),(2837, -342) # Coordinates to check discord message
            
            banned = check_message(ban)
            
            if banned == "banned":
                time.sleep(random.randint(600,900)) # if banned, try it again after few min
                driver.get(url)
            elif banned == "reset":
                pass
            else:
                error_ls.append(appid)
            
            table_check = check_message(updatetable)
            
            if table_check == "Builds":
                start = (2707, -297)
            elif table_check == " Our Discord h":
                start = (2718, -225)
            else:
                start = (2658, -51)
                print(appid, " game name too long, adjust drag point")
                
            update_history = scrape_update(start, appid)
            update_history_df = pd.concat([update_history_df, update_history], axis=0)
            update_history_df.to_pickle("../data/crawled_data/update_history.pickle")
            time.sleep(random.randint(0,3))
        time.sleep(random.randint(360,900))
    driver.quit()    

