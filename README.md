
# Steam Game Data Analysis 

### This project is only for an educational purpose.


# Project structure:
1. Scraping 
    - Modified some Scrapy spiders and code accompanying the *Scraping the Steam Game Store* article published on the [Scrapinghub blog](https://blog.scrapinghub.com/2017/07/07/scraping-the-steam-game-store-with-scrapy/). 
    - Getting data from Steam, SteamDB and Metacritic.
    - It only scrape games on Steam platform based on SteamDB. 
    - SteamDB has unique panel data (price&sale history, update history, number of game players and twitch viewers)

    - To scrape data 
        1. run 'run_steamdb_scraper.sh' 
            - It runs steamdb_scraper.py 
            - It collects data from `SteamDB`. It collects game lists, price history, number of game players and twitch viewers history on game-level.
            - If you want to scrape update history, run steamdb_UH_scraper.py but you need to change coordinates because I used pyautogui. 
        2. run 'run_steam_scrapy.sh'
            - It runs steam products scrapy
            - It collects game infos on Steam website
        3.  run 'metacritic.sh'
            - It collects game infos, reviews and user info on metacritic.com

Scraped data would be like this
<img src = "steam_project_data.png" > 

2. Data Preprocess
    - Cleansing data for analysis.
        - It includes convert data types, unpacking list, split, filtering and aggregate data.

3. Data Analysis
From this dataset, there are plenty subjects to try such as simple prediction, classification, and clustering using ML, text mining, network analysis and reccomendation system.

For my personal project, I researched impact of COVID-19 on game industry. Using extra information and data from Our World in Data.

- Hannah Ritchie, Edouard Mathieu, Lucas Rodés-Guirao, Cameron Appel, Charlie Giattino, Esteban Ortiz-Ospina, Joe Hasell, Bobbie Macdonald, Diana Beltekian and Max Roser (2020) - "Coronavirus Pandemic (COVID-19)". Published online at OurWorldInData.org. Retrieved from: 'https://ourworldindata.org/coronavirus' [Online Resource]

`Main findings`
- COVID-19 has impacted positive effect (increase in number of game players)
on game industry.
- Among characteristics of games, multi-playable games have largest impact.
- However, due to the desire of playing with others, discount effect of multi-playable games is not effective compared to other genres that are significant.


### Structure
```
📦steam_project
 ┣ 📂data
 ┃ ┣ 📂additional_data 
 ┃ ┣ 📂crawled_data                   
 ┃ ┗ 📂preprocessed_data 
 ┃
 ┣ 📂data_analysis
 ┃ ┣ 📜0.preprocess_crawled_data.ipynb
 ┃ ┣ 📜1.Basic_analysis.ipynb
 ┃ ┣ 📜2.Covid19_and_Gameindustry_Report.ipynb
 ┃ ┣ 📜analysis_tool.py # functions for econometric analysis
 ┃ ┗ 📜basic_preprocess.py # Preprocess raw data for analysis
 ┃             
 ┣ 📂metacritic_scraper
 ┃ ┣ 📂metacritic
 ┃ ┃ ┣ 📂spiders
 ┃ ┃ ┃ ┣ 📜product_spider.py           # Scraping product information that were not able to scrape from steam (e.g. ESRB Ratings)
 ┃ ┃ ┃ ┗ 📜user_spider.py              # Scraping user information who wrote and rated games on Steam
 ┃ ┃ ┣ 📜items.py
 ┃ ┃ ┣ 📜metacritic_review_scraper.py  # Scraping using BeautifulSoup and requests. This file in Not a part of scrapy framework. 
 ┃ ┃ ┣ 📜middlewares.py
 ┃ ┃ ┣ 📜pipelines.py
 ┃ ┃ ┗ 📜settings.py
 ┃ ┃
 ┣ 📂steam_scraper
 ┃ ┣ 📂steam
 ┃ ┃ ┣ 📂spiders
 ┃ ┃ ┃ ┗ 📜product_spider.py           # Scraping product informations on steam.
 ┃ ┃ ┣ 📜items.py
 ┃ ┃ ┣ 📜middlewares.py
 ┃ ┃ ┣ 📜pipelines.py
 ┃ ┃ ┣ 📜settings.py
 ┃ ┃ ┣ 📜steamdb_UH_scraper.py         # Scraping update history of each games.
 ┃ ┃ ┗ 📜steamdb_scraper.py            # Scraping SteamDB to collect game lists on steam, price history, number of game players and twitch viewers history data.
 ┣ 📜README.md
 ┣ 📜run_metacritic.sh
 ┣ 📜run_steam_scrapy.sh
 ┗ 📜run_steamdb_scraper.sh
```
 