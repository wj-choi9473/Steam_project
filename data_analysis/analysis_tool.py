
from datetime import timedelta # to calc time
import dateutil.parser

import pandas as pd
import numpy as np
import pickle

import matplotlib as mpl
import matplotlib.pyplot as plt
plt.style.use(["classic"])
plt.rcParams['font.family'] = 'Times New Roman'

import plotly.io as pio 
import plotly.express as px

"""
Functions that frequently needed for analysis
This includes handling, merging and visualizing data
"""

def split_chunk(ls, n):
    """
    split list,df into n elements
    """
    for i in range(0, len(ls), n): 
        yield ls[i:i + n] 

def get_time_index(df, timecol, start, end):
    """
    Return df only wated time period

    timecol: str ; time column name
    start: yyyy-mm-dd
    end: yyyy-mm-dd 
    """
    # set time index
    df = df.set_index(f"{timecol}")
    # set time range 
    df = df.loc[f"{start}":f"{end}"].reset_index()
    return df


def make_time_index(df, time_col,time_index_name=None):
    """
    make time index(e.g. if there are 2 weeks, week1: 0, week2: 1) corresponding to date

    df: dataframe
    time_col: time column name
    """
    time = df[time_col].unique()
    date_dict = dict(zip(time,range(len(time))))
    df["time_index"] = df["time"].map(date_dict)
    if not time_index_name == None:
        df = df.rename(columns={"time_index":time_index_name})
    return df

def get_appdemand_before_after(period, week, date_point):
    """
    period: "D" as day or "W" as week
    week: int;  set date range with week as unit. ex) 3 means bring data 3weeks before and after based on date_point
    date_point: yyyy-mm-dd
    """

    appdemand = pd.read_pickle(f"../data/preprocessed_data/appdemand_{period}.pickle")
    
    date_point = dateutil.parser.parse(date_point)
    before = date_point - timedelta(weeks=week)
    after = date_point + timedelta(weeks=week)

    result_df = get_time_index(appdemand,"time",before,after)

    return result_df

def filter_data(df,release_date,current,review_num):
    """
    Filter data according to parameters

    df: appdemand_df
    release_date: tuple(or list) of date (start,end)  e.g.(2020-01-01,2020-12-31) represents game released during year of 2020
    current: int, recent(current) number of players cutoff 100 means "get games that current numebr of players are more than 100 or equal")
    review_num: int, number of reviews cutoff
    """
    if df["appid"].dtypes != "int64":
        df["appid"] = df["appid"].astype(int)

    game_info = pd.read_pickle("../data/preprocessed_data/game_info.pickle")
    checker_release = list(get_time_index(game_info,"release_date",release_date[0],release_date[1])["appid"])
    df = df[df["appid"].isin(checker_release)]
    
    checker_current = list(game_info[game_info["current"] >= current]["appid"])
    df = df[df["appid"].isin(checker_current)]
    
    metacritic_user_reviews_D = pd.read_pickle("../data/preprocessed_data/metacritic_user_reviews_D.pickle")
    review_count = metacritic_user_reviews_D.groupby(by="appid")["rating"].count().reset_index()
    checker_review = list(review_count[review_count["rating"] >= review_num]["appid"].astype(int))
    df = df[df["appid"].isin(checker_review)]
    df["appid"] = df["appid"]
    return df

def draw_lineplots(*df,label,title=None,dx,dy,xlabel=None, ylabel=None, vline=None):
    """
    Draw multiple line plots in one figure
    df: dfs for plotting,
    label: label for each line
    title: title of graph 
    dx: x coordinate str
    dy: y coordinatestr 
    xlabel:xlabel
    ylabel:ylabel
    vline: list [location,color,label] vertical line 
    """
    fig, ax = plt.subplots()
    for i in range(len(df)):
        ax.plot(df[i][[dx]],df[i][dy],marker="o", label=label[i])


    ax.axvline(x=vline[0], color=vline[1], label=vline[2]) if vline != None else None
    ax.set_title(title) if title != None else None 
    ax.set_xlabel(xlabel) if xlabel != None else None
    ax.set_ylabel(ylabel) if xlabel != None else None
    ax.grid(False)
    ax.legend(
            loc="upper center", bbox_to_anchor=(0.5, -0.1), fancybox=True, shadow=True, ncol=5
            )
    return fig

def draw_trend_plot(df,genre):
    """
    draw trend plot according to chrateristic of duumy variable
    df:
    genre: str; column that indicates dummy
    """
    df_1 = df[df[genre] == 1]
    df_2 = df[df[genre] == 0]
    
    df_1_agg = df_1.groupby("time").mean().reset_index()
    df_2_agg = df_2.groupby("time").mean().reset_index()
    fig = px.line()
    fig.add_scatter(x=df_1_agg["time"], y=df_1_agg["discount_rate"], mode="lines", name=genre+"== 1")
    fig.add_scatter(x=df_2_agg["time"], y=df_2_agg["discount_rate"], mode="lines", name=genre+"== 0")
    return fig

def make_did_data_panel(treat_df,control_df,shock):
    """
    aggregate treatment group and control group 
    return Treated + After + Covariates.
    It does return DID coef(interaction term of Treat X After)
    because it cab be easily generate through linear model using formula api.
    
    treat_df: df with treatment group
    control_df: df with control group
    entity: individual id, index
    shock: exogenous shock time to indicate before&after str e.g. "2020-03-11" 
    """
    
    treat_df = make_time_index(treat_df,"time")
    control_df = make_time_index(control_df,"time")
    # add 1000000 on appid for control group
    control_df["appid"] = control_df["appid"] + 1000000
    # code treat group 1, control group 0
    treat_df["Treated"] = 1
    control_df["Treated"] = 0
    df = pd.concat([treat_df, control_df])
    
    #find time_index which is exogenous shock
    after = treat_df[treat_df["time"] == shock]["time_index"].unique()[0]
    #assign after 1 or 0 
    condls = [df["time_index"] >= after, df["time_index"] < after]
    choicels = [1, 0]
    df["After"] = np.select(condls, choicels, default=2).astype(int)
    
    return df

    
def load_did_data(timeunit, bumper = True):
    """
    Load data for DID,DDD
    Dataset is consists of only paidapp, currently 100 more or equal players are playing, and have 5 or more reviews
    time period (matched weekday and weekend)
    control: 2019-01-06 ~ 2019-12-22
    treat(COVID-19 year): 2020-01-05 ~ 2020-12-20
    

    timeunit: "D" or "W" daily데이터 인지 week인지 
    bumper: 3/12~22 데이터 제거 여부

    """
    # Load datasets
    game_info = pd.read_pickle("../data/preprocessed_data/game_info.pickle")

    price_sale_D = pd.read_pickle("../data/preprocessed_data/price_sale_D.pickle")
    price_sale_W = pd.read_pickle("../data/preprocessed_data/price_sale_W.pickle") 

    appdemand_D = pd.read_pickle("../data/preprocessed_data/appdemand_D.pickle")
    appdemand_D["appid"] = appdemand_D["appid"].astype(int)
    appdemand_W = pd.read_pickle("../data/preprocessed_data/appdemand_W.pickle")
    appdemand_W["appid"] = appdemand_W["appid"].astype(int)
    # Load paid game list
    with open("paid_games_ls.pickle","rb") as f:
        paid_games_ls = pickle.load(f)
    update_history = pd.read_pickle("../data/preprocessed_data/update_history_D.pickle")
    update_history_W = pd.read_pickle("../data/preprocessed_data/update_history_W.pickle")
    # Load review panel data
    rev_D = pd.read_pickle("../data/preprocessed_data/review_D.pickle")
    rev_D["appid"] = rev_D["appid"].astype(int)

    rev_W = pd.read_pickle("../data/preprocessed_data/review_W.pickle")
    rev_W["appid"] = rev_W["appid"].astype(int)

    if timeunit == "D":
        ps_appdemand_D = appdemand_D[appdemand_D["appid"].isin(paid_games_ls)]
        # merge infos
        D_price_filter = filter_data(price_sale_D,("1900-01-01","2021-12-12"),current=100,review_num=5)
        D_price_filter_info = pd.merge(D_price_filter,game_info,how="left", on="appid")
        price_value_filter_info = pd.merge(ps_appdemand_D,D_price_filter_info,how="left", on=["appid","time"])
        # merge update info
        price_value_filter_info = pd.merge(price_value_filter_info,update_history[["DATE","appid","update","update_cum"]],
        how="left", left_on=["appid","time"], right_on=["appid","DATE"])
        price_value_filter_info["update"] = price_value_filter_info["update"].fillna(value=0)

        price_value_filter_info["update_cum"] = price_value_filter_info.groupby(["appid"])["update_cum"].fillna(method="ffill")
        price_value_filter_info["update_cum"] = price_value_filter_info["update_cum"].fillna(value=0)
        #merge review info
        price_value_filter_info = pd.merge(price_value_filter_info, rev_D, how="left", left_on = ['appid','time'], right_on = ["appid","date"])

        price_value_filter_info["num_of_reviews"] = price_value_filter_info["num_of_reviews"].fillna(value=0)

        price_value_filter_info["num_of_reviews_cum"] = price_value_filter_info.groupby(["appid"])["num_of_reviews_cum"].fillna(method="ffill")
        price_value_filter_info["num_of_reviews_cum"] = price_value_filter_info["num_of_reviews_cum"].fillna(value=0)

        price_value_filter_info["rating_cum_mean"] = price_value_filter_info.groupby(["appid"])["rating_cum_mean"].fillna(method="ffill")


    elif timeunit == "W":
        
        ps_appdemand_W = appdemand_W[appdemand_W["appid"].isin(paid_games_ls)]

        W_price_filter = filter_data(price_sale_W,("1900-01-01","2021-12-12"),current=100,review_num=5)
        W_price_filter_info = pd.merge(W_price_filter,game_info,how="left", on="appid")
        price_value_filter_info = pd.merge(ps_appdemand_W,W_price_filter_info,how="left", on=["appid","time"])

        price_value_filter_info = pd.merge(price_value_filter_info,update_history_W,
        how="left", left_on=["appid","time"], right_on=["appid","DATE"])
        price_value_filter_info["update"] = price_value_filter_info["update"].fillna(value=0)

        price_value_filter_info["update_cum"] = price_value_filter_info.groupby(["appid"])["update_cum"].fillna(method="ffill")
        price_value_filter_info["update_cum"] = price_value_filter_info["update_cum"].fillna(value=0)

        price_value_filter_info = pd.merge(price_value_filter_info, rev_W, how="left", left_on = ['appid','time'], right_on = ["appid","date"])

        price_value_filter_info["num_of_reviews"] = price_value_filter_info["num_of_reviews"].fillna(value=0)

        price_value_filter_info["num_of_reviews_cum"] = price_value_filter_info.groupby(["appid"])["num_of_reviews_cum"].fillna(method="ffill")
        price_value_filter_info["num_of_reviews_cum"] = price_value_filter_info["num_of_reviews_cum"].fillna(value=0)

        price_value_filter_info["rating_cum_mean"] = price_value_filter_info.groupby(["appid"])["rating_cum_mean"].fillna(method="ffill")

    else:
        raise ValueError("timeunit should be either D or W")

    if bumper == True:
        # control 2019-3-13~2019-3-24
        control_before = get_time_index(price_value_filter_info, "time", "2019-01-06","2019-03-13")
        control_after = get_time_index(price_value_filter_info, "time", "2019-03-25","2019-12-22")
        control = pd.concat([control_before,control_after], axis = 0)
        # treat 2020-3-11일~2020-3-22
        treat_before = get_time_index(price_value_filter_info, "time", "2020-01-05","2020-03-11")
        treat_after = get_time_index(price_value_filter_info, "time", "2020-03-23","2020-12-20")
        treat = pd.concat([treat_before,treat_after], axis = 0)
    else:
        control = get_time_index(price_value_filter_info, "time", "2019-01-06","2019-12-22")
        treat = get_time_index(price_value_filter_info, "time", "2020-01-06","2020-12-20")

    # time_index for DD,DDD
    control = make_time_index(control,"time")
    treat = make_time_index(treat,"time")

    if timeunit == "D":
        test = make_did_data_panel(treat,control, shock = "2020-03-11")
    elif timeunit == "W":
        test = make_did_data_panel(treat,control, shock = "2020-03-08")
    else:
        raise ValueError("timeunit should be either D or W")

    # Variable for released days
    test["released"] = test["time"] - test["release_date"]
    test["released"] = test["released"].dt.days

    # exclud turn free games
    test = test[test["turn_free_game"] == 0]

    return test

def make_event_dummy(df,after):
    """
    make dummy time variable 
    after: int; time_index for dataset
    """
    # unit of analysis is day but make 7days shock as one dummy variable
    df[f"After_{round((after-65)/7)}"] = np.where((df["time_index"]>=after)&(df["time_index"]<after+7), 1,0)
    return df


def summary_report(res):
    """
    model estimation summary
    
    Returns summary result suitable for report
    """
    def p_value_trans(x):
        if x < 0.01:
            x = "***"
        elif x < 0.05:
            x = "**"
        elif x < 0.10:
            x = "*"
        else:
            x = " "
        return x

    DDD_result_df = pd.DataFrame({
    "coef":round(res.params,4),
    "std":round(res.std_errors,4),
    "p-value":round(res.pvalues,4)
})
    DDD_result_df["report"] = DDD_result_df["coef"].astype(str) + DDD_result_df["p-value"].apply(p_value_trans) + " (" + DDD_result_df["std"].astype(str) + ")"
    
    DDD_info_df = pd.DataFrame({
    "Entities":res.entity_info["total"],
    "obervations":res.nobs,
    "R-squared(Within)":round(res.rsquared_within,4)
    },index=["info"])
    
    
    return DDD_info_df, DDD_result_df
    