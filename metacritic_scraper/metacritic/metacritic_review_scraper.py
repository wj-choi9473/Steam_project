import time
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def make_url_name(name):
    name = str(name)
    name = name.replace(" ", "-")
    name = name.replace(":", "")
    name = name.replace("'", "")
    name = name.replace("&amp;", "and")
    name = name.replace(",", "")
    name = name.replace(".", "")
    return name.lower()

def make_urls_page(): 
    """
    Return url and number of pages for each url
    result would look like this [('game1','10'),('game2','5')...]
    """
    appnames = pd.read_pickle("/Users/wonjae/Google Drive/steam_project/data/crawled_data/applist.pickle")["appname"].apply(make_url_name)
    urls = [f"https://www.metacritic.com/game/pc/{appname}/user-reviews?sort-by=date&num_items=100&page=0" for appname in appnames]

    
    last_pages = []
    names = []

    print("*"*30+"Finding Last Pages"+"*"*30)
    for url in tqdm(urls, desc ="Finding Last Pages"):
        headers = {"user-agent": UserAgent().chrome}
        response = requests.get(url, headers=headers)
        if str(response) == "<Response [200]>":
            doc = BeautifulSoup(response.content, "html.parser")

            last_page_selector = "#main > div.partial_wrap > div.module.reviews_module.user_reviews_module > div > div.page_nav > div > div.pages > ul > li.page.last_page > a"

            try:
                last_page = doc.select(last_page_selector)[0].text
            except:
                last_page = 1
            appname = url.split("/")[5]
            last_pages.append(last_page)
            names.append(appname)
            print(appname,":",last_page)
            time.sleep(0.2)
        else:
            print("*"*60)
            print(url.split("/")[5],":",str(response))
            print("*"*60)

    name_page = list(zip(names, last_pages))
    return name_page


def get_user_reviews(name_page):
    """
    Scrape data from metacritic.com
    name_page: list
    """

    review_dict = {"metacritic_name": [], "user_name": [], "date": [], "rating": [], "review": []}

    print("*"*30+"Scraping data"+"*"*30)
    for name, page in tqdm(name_page, desc="Progress in Game Level"):
        print("start: ",name)
        for p in tqdm(range(int(page)), desc = "Progress in Page Level"):
            url = f"https://www.metacritic.com/game/pc/{name}/user-reviews?sort-by=date&num_items=100&page={p}"
            user_agent = {"User-agent": UserAgent().chrome}
            response = requests.get(url, headers=user_agent)

            soup = BeautifulSoup(response.text, "html.parser")
            for review in soup.find_all("div", class_="review_content"):
                review_dict["metacritic_name"].append(name)
                if review.find("div", class_="name") == None:
                    break
                try:
                    review_dict["user_name"].append(
                        review.find("div", class_="name").find("a").text
                    )
                except:
                    review_dict["user_name"].append(np.nan)
                try:
                    review_dict["date"].append(review.find("div", class_="date").text)
                except:
                    review_dict["date"].append(np.nan)

                try:
                    review_dict["rating"].append(
                        review.find("div", class_="review_grade").find_all("div")[0].text
                    )
                except:
                    review_dict["rating"].append(np.nan)

                if review.find("span", class_="blurb blurb_expanded"):
                    try:
                        review_dict["review"].append(
                            review.find("span", class_="blurb blurb_expanded").text
                        )
                    except:
                        review_dict["review"].append(np.nan)
                else:
                    try:
                        review_dict["review"].append(
                            review.find("div", class_="review_body").find("span").text
                        )
                    except:
                        review_dict["review"].append(np.nan)

        metacritic_user_reviews = pd.DataFrame.from_dict(review_dict, orient="index").T
        metacritic_user_reviews.to_pickle("../data/crawled_data/metacritic_user_reviews.pickle")
        metacritic_user_reviews.to_csv("../data/crawled_data/metacritic_user_reviews.csv",index=False)
    return metacritic_user_reviews



if __name__ == "__main__":
    name_page = make_urls_page()
    metacritic_user_reviews = get_user_reviews(name_page)
    metacritic_user_reviews.to_pickle("../data/crawled_data/metacritic_user_reviews.pickle")
    metacritic_user_reviews.to_csv("../data/crawled_data/metacritic_user_reviews.csv",index=False)
    