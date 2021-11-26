import numpy as np
import pandas as pd
from tqdm import tqdm

# language detect if need
import googletrans
from googletrans import Translator
# random user agent using it with googletrans
from fake_useragent import UserAgent

"""
Aggregate appinfo dataset: game_info_preprocess() -> game_info.pickle  
Resample appdemand data: appdemand_preprocess() -> appdemand_{period}.pickle
Fill omitted time in price, discount: price_sale_preprocess(), make_daily_price() -> price_sale_D.pickle
Preprocess update history data: update_history_preprocess() -> update_history.pickle
Preprocess update history data into panel data i for each game in t time: update_to_panel() -> update_history_{period}.pickle
Preprocess Review data: metacritic_user_reviews_preprocess() -> metacritic_user_reviews_{period}.pickle
Preprocess Review data into panel data i for each game in t time: review_to_panel() -> review_{period}.pickle

Language detection and translate was intend to do some textmining analysis.
However, I didn't do this part because I do not need this part for my analysis. 
"""

def to_list_element(df_col):
    """
    List values(e.g. Audio-or video tags, lists of all authors) to actural list data type in one element
    df_col: DataFrame column or item lists
    """
    df_col = df_col.astype(str)
    return df_col.apply(lambda x: x.split(","))

def list_value_count(df_col, normalize = False, col_name=None):
    """
    Getting unique value
    df_col: DataFrame column or item lists
    normalize: bool
    col_name: int,str
    """
    if col_name == None:
        col_name = df_col.name
    else:
        col_name = col_name
    count_df = pd.DataFrame()
    for i in range(df_col.shape[1]):
        if normalize == True:
            df1 = pd.DataFrame(df_col.iloc[:,i].value_counts(normalize = True)).reset_index().rename(columns={'index':col_name})
        else :
            df1 = pd.DataFrame(df_col.iloc[:,i].value_counts()).reset_index().rename(columns={'index':col_name})
        count_df = pd.concat([count_df,df1],axis=1)
    return count_df 

def make_list_to_dummy(df_col, option = "int"):
    """
    Unpack list values in one element
    df_col: DataFrame column or item lists
    """
    # create empty list,dict
    unique_values = []
    bool_dict = {}
    
    item_lists = df_col.apply(pd.Series)
    for i in range(item_lists.shape[1]):
        for value in item_lists[i].unique():
            unique_values.append(value)
    unique_values = list(set(unique_values)) 
    
    for i, item in enumerate(unique_values):
        bool_dict[item] = df_col.apply(lambda x: item in x)
    
    if option == "int":
        return pd.DataFrame(bool_dict).astype(int)
    elif option == "bool":
        return pd.DataFrame(bool_dict)
    else:
        raise ValueError("option must be int or bool")

def game_info_preprocess(save=True):
    """
    aggregate appinfo dataset
    save: bool ; save if True, return df if False. Defalut True
    """
    applist = pd.read_pickle("../data/crawled_data/applist.pickle")
    appinfo = pd.read_csv("../data/crawled_data/appinfo.csv")
    big_pubs = pd.read_csv("../data/additional_data/bigpublishers.csv")

    # change data type to int
    applist_cols = ["appid","alltimepick","current"]
    applist[applist_cols] = applist[applist_cols].astype(int)
    # appinfo preprocess
    appinfo_cols = ['appid','title','release_date', 'genres', 'developer', 'publisher', 'specs', 'user_tags', 'sys_requirement']
    appinfo = appinfo[appinfo_cols]
    appinfo = appinfo[appinfo["release_date"] != "Soon"] # select only released game
    appinfo["release_date"] = pd.to_datetime(appinfo["release_date"], infer_datetime_format=True) # release_date to datetime

    genre_cols = ["Action", "Indie", "Strategy", "Early Access", "Adventure", "Casual", "Simulation", "RPG", "Free to Play", "Racing"]
    appinfo["genres"] = to_list_element(appinfo["genres"])
    dummy_cols= make_list_to_dummy(appinfo["genres"])[genre_cols]
    appinfo = pd.concat([appinfo,dummy_cols],axis=1)

    spec_cols = ["Single-player", "Online PvP", "MMO", "Cross-Platform Multiplayer","Online Co-op"]
    appinfo["specs"] = to_list_element(appinfo["specs"])
    dummy_cols= make_list_to_dummy(appinfo["specs"])[spec_cols]
    appinfo = pd.concat([appinfo,dummy_cols],axis=1)

    tag_cols = ["Multiplayer", "Co-op"]
    appinfo["user_tags"] = to_list_element(appinfo["user_tags"])
    dummy_cols= make_list_to_dummy(appinfo["user_tags"])[tag_cols]
    appinfo = pd.concat([appinfo,dummy_cols],axis=1)

    condition = (appinfo["Online PvP"]==1) | (appinfo["MMO"] == 1) | (appinfo["Cross-Platform Multiplayer"] == 1)| (appinfo["Online Co-op"] == 1)| (appinfo["Multiplayer"] == 1) | (appinfo["Co-op"] == 1)

    appinfo["playwithother"] = np.where(condition, 1,0)

    # add big publisher data
    pubs = list(big_pubs["bigpublishers"])
    appinfo["bigpublishers"] = appinfo["publisher"].isin(pubs).astype(int)
    # merge data
    appinfo = pd.merge(applist,appinfo, how="inner", on="appid")
    if save == True:
        appinfo.to_pickle("../data/preprocessed_data/game_info.pickle")
        appinfo.to_csv("../data/preprocessed_data/game_info.csv",index=False)
    elif save == False:
        return appinfo
    else:
        raise ValueError("value should be Boolean")

def appdemand_preprocess(period, save=True):
    """
    period: datetime like str "D","W","M"
    save: bool ; save if True, return df if False. Defalut True
    """
    df = pd.read_pickle("../data/crawled_data/appdemand.pickle")
    
    # check time period: day, week, month
    if period == "D":
        df = df
    else:
        df = df.groupby(by="appid").resample(period,on="time").mean().reset_index()

    # calc daily market size
    total = df.groupby("time").sum().reset_index()[["time","value","values_twitch"]]
    total = total.rename(columns={'value':"total_value",'values_twitch':"total_values_twitch"})
    # merge market size
    df = pd.merge(df,total, how="left", on="time")

    # calc market_share
    df["market_share"] = df["value"]/df["total_value"]
    df["market_share_twitch"] = df["values_twitch"]/df["total_values_twitch"]
    if save == True:
        df.to_pickle(f"../data/preprocessed_data/appdemand_{period}.pickle")
        df.to_csv(f"../data/preprocessed_data/appdemand_{period}.csv",index=False)
    elif save == False:
        return df
    else:
        raise ValueError("save parameter should be Boolean")

def fill_time(df, appid):
    """
    Fill ommited time period
    df: price_sale DataFrame
    appid: individual appid
    """
    reidx_df = df[df.index == appid].reset_index()

    # start time
    start = df[df.index == appid]["time"].iloc[0]
    # end time
    end = df[df.index == appid]["time"].iloc[-1]
    days = pd.DataFrame(pd.date_range(start, end, freq="D")).rename(columns={0:"time"})
    full_period = pd.merge(days,reidx_df, how="left",on="time")
    full_period[["appid","price","price_us","discount_rate","release_price","release_discount_rate"]] = full_period[["appid","price","price_us","discount_rate","release_price","release_discount_rate"]].fillna(method="ffill")
    return full_period

def price_sale_preprocess(save=True):
    """
    return 2 types of df:
    1. original panel df with preprocessed
    2. df that fill ommited time period for all individual game (daily)
    save: bool ; save if True, return df if False. Defalut True
    """
    # dataset load
    price_sale = pd.read_pickle("../data/crawled_data/price_sale.pickle")
    price_sale["appid"] = price_sale["appid"].astype(int)
    price_sale["time"] = pd.to_datetime(price_sale["time"], infer_datetime_format=True)
    
    game_info = pd.read_pickle("../data/preprocessed_data/game_info.pickle")
    # currently free game list: 460 among 3518
    current_free = game_info[game_info["Free to Play"] == 1]["appid"].unique()
    
    # for each appid, filter price history record more than 1 and price is 0 on last date
    turn_free_df = pd.DataFrame() # games that turn free and keep it free

    for appid in price_sale["appid"].unique():
        price_history = price_sale[price_sale["appid"] == appid].shape[0]
        last_day = price_sale[price_sale["appid"] == appid][-1:]
        last_price = float(last_day["price"][-1:])
        
        if (price_history > 1) & (last_price == 0):
            turn_free_df = pd.concat([turn_free_df,last_day])
    # turn free game lists
    turn_free = turn_free_df["appid"].unique() 
    # originally freegame = difference of sets of currently freegame, turn free game.
    originally_free= np.setdiff1d(current_free,turn_free)
    # price_sale history df excluding originally free games
    price_sale_adj_df= price_sale[~price_sale["appid"].isin(originally_free)]
    original_price_adj_df = price_sale_adj_df[price_sale_adj_df["discount_rate"] == 0].drop_duplicates(subset = ["price","appid"])


    # free games
    free_game_df = pd.DataFrame()

    for appid in original_price_adj_df["appid"].unique():
        history = original_price_adj_df[original_price_adj_df["appid"] == appid].shape[0]
        
        if history == 1:
            price_check = float(original_price_adj_df[original_price_adj_df["appid"] == appid]["price"])
            
            if price_check == 0.0:
                free_game_df = pd.concat([free_game_df,original_price_adj_df[original_price_adj_df["appid"] == appid]])      

    orignally_free_games_ls = list(originally_free)
    # include free games in list
    orignally_free_games_ls.extend(list(free_game_df["appid"]))

    # only contain paid game's price sale history (exclude turn free, originally free games)
    price_sale_adj2_df= price_sale[~price_sale["appid"].isin(orignally_free_games_ls)]


    # get original price
    original_price_adj2_df = price_sale_adj2_df[price_sale_adj2_df["discount_rate"] == 0].drop_duplicates(subset = ["price","appid"])

    # get released price
    release_price_df = original_price_adj2_df.drop_duplicates(subset = ["appid"])
    # Dataset without orginally freegame (price, discount records in each turning point)
    price_sale_adj2_df = pd.merge(price_sale_adj2_df,release_price_df[["appid","price"]], how= "left", on="appid").rename(columns={"price_x":"price",
                                                                                                        "price_y":"release_price"})
    # discount rate based on released price
    price_sale_adj2_df["release_discount_rate"]= round(1 - (price_sale_adj2_df["price"]/price_sale_adj2_df["release_price"]),2) * 100

    # update gameinfo
    game_info["originally_free_game"] = np.where(game_info["appid"].isin(orignally_free_games_ls),1,0)
    game_info["turn_free_game"] = np.where(game_info["appid"].isin(turn_free),1,0)
    game_info = pd.merge(game_info, turn_free_df[["appid","time"]], how="left",on="appid").rename(columns={"time":"turn_free_time"})


    if save == True:
        price_sale_adj2_df.to_pickle("../data/preprocessed_data/price_sale_adj.pickle")
        game_info.to_pickle("../data/preprocessed_data/game_info.pickle")
    elif save == False:
        return price_sale_adj2_df, game_info
    else:
        raise ValueError("value should be Boolean")

def make_daily_price(df, save=True):
    """
    Make daily price
    df: price_sale_history dataframe
    """
    df = df.set_index("appid")
    appids = df.index.unique()

    price_sale_df = pd.DataFrame()

    for appid in tqdm(appids):
        df_appid = fill_time(df,appid)
        price_sale_df = pd.concat([price_sale_df,df_appid])
    
    if save == True:
        price_sale_df.to_pickle("../data/preprocessed_data/price_sale_D.pickle")
    elif save == False:
        return price_sale_df
    else:
        raise ValueError("value should be Boolean")

def update_history_preprocess(save=True):
    """
    Change date to datetime
    save: bool ; save if True, return df if False. Defalut True
    """
    update_history = pd.read_pickle("../data/crawled_data/update_history.pickle")
    update_history["DATE"] = pd.to_datetime(update_history["DATE"], infer_datetime_format=True)
    update_history["update"] = 1
    update_history["update_cum"]= update_history[["appid","DATE","update"]].groupby(["appid"]).cumcount(ascending=False) + 1
    
    if save == True:
        update_history.to_pickle("../data/preprocessed_data/update_history.pickle")
        update_history.to_csv("../data/preprocessed_data/update_history.csv",index=False)
    elif save == False:
        return update_history
    else:
        raise ValueError("value should be Boolean")

def make_url_name(name):
    name = str(name)
    name = name.replace(" ", "-")
    name = name.replace(":", "")
    name = name.replace("'", "")
    name = name.replace("&amp;", "and")
    name = name.replace(",", "")
    name = name.replace(".", "")
    return name.lower()

def panel_cum_mean(df):
    """
    Calc cumulative mean

    df: df for resampling
    """
    copy = df.dropna()
    copy["cumcount"] = copy.groupby(by="metacritic_name").cumcount()
    copy["cumsum"] = copy.groupby(by="metacritic_name")["rating"].cumsum()
    copy["rating_cummean"] = (copy["cumsum"]) / (copy["cumcount"] + 1)
    copy = copy.drop(labels=["rating", "cumcount", "cumsum"], axis=1)

    df = pd.merge(df, copy, how="outer", on=["metacritic_name", "date"])
    df["rating_cummean"] = df.groupby(by="metacritic_name")["rating_cummean"].fillna(method="ffill")
    return df["rating_cummean"]

def metacritic_user_reviews_preprocess(period, save=True):
    """
    period: datetime like str "D","W","M"
    save: bool ; save if True, return df if False. Defalut True
    """
    applist = pd.read_pickle("../data/crawled_data/applist.pickle")
    applist["metacritic_name"]= applist["appname"].apply(make_url_name)

    df = pd.read_pickle("../data/crawled_data/metacritic_user_reviews.pickle")
    df.dropna(inplace=True)

    df["rating"] = df["rating"].astype(int)
    df["date"] = pd.to_datetime(df["date"], infer_datetime_format=True)
    

    if period != "D":
        df = df.groupby("metacritic_name").resample(period,on="date").mean().reset_index()
        df["cum_mean"]= panel_cum_mean(df)
        df = pd.merge(df,applist[["metacritic_name",'appid']], how='inner', on="metacritic_name")
    else:
        df = pd.merge(df,applist[["metacritic_name",'appid']], how='inner', on="metacritic_name")

    if save == True:
        df.to_pickle(f"../data/preprocessed_data/metacritic_user_reviews_{period}.pickle")
        df.to_csv(f"../data/preprocessed_data/metacritic_user_reviews_{period}.csv",index=False)
    elif save == False:
        return df
    else:
        raise ValueError("value should be Boolean")

def review_to_panel(save = True):
    """
    Preprocess review data into panel data i for each game in t time

    save: bool ; save if True, return df if False. Defalut True
    """
    reviews_D = metacritic_user_reviews_preprocess("D", save = False)
    # make daily review dataframe
    reviews_D_test = pd.DataFrame(reviews_D.groupby(["appid","date"])["rating"].count()).reset_index().rename(columns={"rating":"num_of_reivews"})

    reviews_D_test["rating_day_mean"] = reviews_D.groupby(["appid","date"])["rating"].mean().reset_index()["rating"]
    # get cum count review number
    reviews_D_test["num_of_reivews_cum"] = reviews_D_test.groupby(by="appid")["num_of_reivews"].cumsum()
    # get cum review rating mean
    reviews_D_test["rating_cum_mean"]= reviews_D_test.groupby(by="appid")["rating_day_mean"].cumsum()/ (reviews_D_test.groupby(by=["appid"]).cumcount()+1)

    # resample number of reviews in week
    reviews_W_test = pd.DataFrame(reviews_D.groupby("appid").resample("W",on="date").sum().reset_index()[["appid","date","num_of_reivews"]])

    # resamle rating mean in week
    reviews_W_test["rating_week_mean"] = reviews_D.groupby("appid").resample("W",on="date").mean().reset_index()["rating_day_mean"]

    # resample num of reviews cum in week
    reviews_W_test["num_of_reviews_cum"] = reviews_W_test.groupby(by="appid")["num_of_reivews"].cumsum()

    # resample rating cum mean in week
    reviews_W_test["rating_cum_mean"] = reviews_W_test.groupby(by="appid")["rating_week_mean"].cumsum()/ (reviews_W_test.groupby(by=["appid"]).cumcount()+1)
    if save == True:
        reviews_D_test.to_pickle("../data/preprocessed_data/review_D.pickle")
        reviews_W_test.to_pickle("../data/preprocessed_data/review_W.pickle")
    else:
        return reviews_D_test,reviews_W_test

def update_to_panel(save = True):
    """
    Preprocess update data into panel data i for each game in t time

    save: bool ; save if True, return df if False. Defalut True
    """
    update_history = pd.read_pickle("../data/preprocessed_data/update_history_D.pickle")
    update_history = update_history.drop_duplicates(["appid","DATE"])
    update_history["update"] = 1
    update_history["update_cum"]= update_history[["appid","DATE","update"]].groupby(["appid"]).cumcount(ascending=False) + 1

    # resample in week
    update_history_W = update_history.groupby("appid").resample("W",on="DATE").count()["update"].reset_index()
    update_history_W["update_cum"]= update_history_W.groupby(["appid"])["update"].cumsum()
    
    if save == True:
        update_history.to_pickle("../data/preprocessed_data/update_history_D.pickle")
        update_history_W.to_pickle("../data/preprocessed_data/update_history_W.pickle")
    else:
        return update_history,update_history_W


##################################################
# Language detect & translate
##################################################
def detect_toEN(text, option):
    """ 
    Language detection & Translation using googletrans.
    text: 'str'
    option: 'str' detect or toEN
    """
    google_trans_urls = ["translate.google.com", "translate.google.co.kr"]
    translator = Translator(service_urls=google_trans_urls, user_agent=UserAgent().chrome)
    if option == "detect":
        try:
            lang = translator.detect(text)
            return lang.lang
        except:
            return np.nan
            
    elif option == "toEN":
        try:
            lang = translator.detect(text)
            if lang.lang != "EN":
                translations = translator.translate(text)
                return translations.text
            else:
                return text
            
        except:
            return np.nan

def metacritic_user_reviews_language(save = True):
    metacritic_user_reviews = pd.read_pickle("../data/crawled_data/metacritic_user_reviews.pickle")
    metacritic_user_reviews["language"] = metacritic_user_reviews["review"].apply(lambda x : detect_toEN(x, option= "detect"))
    metacritic_user_reviews["review_EN"] = metacritic_user_reviews["review"].apply(lambda x : detect_toEN(x, option= "toEN"))
    if save == True:
        metacritic_user_reviews.to_pickle("../data/preprocessed_data/metacritic_user_reviews.pickle")
        metacritic_user_reviews.to_csv("../data/preprocessed_data/metacritic_user_reviews.csv",index=False)
    elif save == False:
        return metacritic_user_reviews
    else:
        raise ValueError("value should be Boolean")

if __name__ == "__main__":
    game_info_preprocess()
    appdemand_preprocess("D")
    appdemand_preprocess("W")
    price_sale_preprocess()
    # price_sale daily
    df = pd.read_pickle("../data/preprocessed_data/price_sale_adj.pickle")
    make_daily_price(df,save=True)
    # price_sale weekly
    price_sale_D = pd.read_pickle("../data/preprocessed_data/price_sale_D.pickle") 
    price_sale_W = price_sale_D[["time","appid","price","discount_rate"]].groupby("appid").resample("W",on="time").mean()
    price_sale_W = price_sale_W[["price","discount_rate"]].reset_index()
    price_sale_W.to_pickle("../data/preprocessed_data/price_sale_W.pickle")

    update_history_preprocess()
    metacritic_user_reviews_preprocess("D")
    metacritic_user_reviews_preprocess("W")
    review_to_panel()
    update_to_panel()

    