'''
    Crypto_Prices_Predicting_Project
    Summer 2022

    Scrape the last 1000 tweets with hashtag $ETH.X posted on Stocktwits
    Extract "emotion" from posts and try to fill empty bull/bear tags

    Hongyan Yang
'''


import os
import csv
import time
import datetime
import numpy as np
import pandas as pd
import text2emotion as te

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

CWD = os.getcwd()
CRYPTO = "ETH.X"
TIME_FORMAT = "%m/%d/%Y, %H:%M:%S"
NOW = datetime.datetime.now()

POSTS_CLASS = "st_24ON8Bp st_1x3QBA7 st_1SZeGna st_3-tdfjd"
HEADER_CLASS = "st_2q3fdlM st_jGV698i st_2-AYUR9 st_2HqScKh st_3QTv-Ni"
USER_NAME_CLASS = "st_x9n-9YN st_2LcBLI2 st_1vC-yaI st_1VMMH6S"
SENTIMENT_CLASS = "lib_XwnOHoV lib_3UzYkI9 lib_lPsmyQd lib_2TK8fEo"
TIME_STAMP_CLASS = "st_28bQfzV st_1E79qOs st_3TuKxmZ st_1VMMH6S"
CONTENT_CLASS = "st_3SL2gug"
RATE_CLASS = "st_2zcZsOz st_VNaOUo1"

def get_html(num_scroll = 150):
    '''
    Apply Selenium to scrape tweets on Stocktwits and generate an html file
    '''
    chrome_driver = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = chrome_driver)
    driver.get("https://stocktwits.com/symbol/" + CRYPTO)
    time.sleep(3)
    scroll_script = "window.scrollTo(0, document.documentElement.scrollHeight)"
    get_height_script = "return document.documentElement.scrollHeight"
    height = driver.execute_script(get_height_script)
    scroll_count = 0
    while scroll_count <= num_scroll:
        driver.execute_script(scroll_script)
        time.sleep(3)
        new_height = driver.execute_script(get_height_script)
        scroll_count += 1
        # Break the loop if reach the end of web page
        if new_height == height:
            break
    # Create an html file to record the scraped tweets
    with open(f"tweets_scrape_{CRYPTO}.html", "w", encoding = "utf-16") as f:
        f.write(driver.page_source)
    driver.close()

def predict_sentimet(database = CWD + "/tweets_database.csv"):
    '''
    Fit L2-reg Logistic Regression with emotions on market sentiment, report
    performance and return the classifier 
    '''
    df = pd.read_csv(database, encoding = "utf-16", delimiter = "\t")
    df["Sentiment"].replace('', np.nan, inplace = True)
    df.dropna(subset = ["Sentiment"], inplace = True)   # Delete rows with na
    vectors = df[["Angry", "Fear", "Happy", "Sad", "Surprise"]].to_numpy()
    labels = (df["Sentiment"] == "Bullish").astype(int).to_numpy()
    # Create training datasets and testing datasets
    data = train_test_split(vectors, labels, test_size = 0.25)
    train, test, train_labels, test_labels = data
    clf = LogisticRegression(penalty = "l2", solver = "lbfgs", tol = 1e-4,
                             max_iter = 300)
    clf.fit(train, train_labels)
    score = clf.score(test, test_labels)    # Report model's performance
    clf.fit(vectors, labels)    # Train model on the full datasets again
    return score, clf

def parse_html(classifier, fill_na = True, limit = 1000):
    '''
    Parse the scraped html file to get text of tweets including time stamps,
    user name, bull/bear tags
    Extract emotion from posts and try to fill empty bull/bear tags
    '''
    # Parse html file with BeautifulSoup
    with open(f"tweets_scrape_{CRYPTO}.html", "r", encoding = "utf-16") as f:
        doc = BeautifulSoup(f, "lxml")
    # Get all post objects
    posts = doc.find_all("div", class_ = POSTS_CLASS, limit = limit)
    if fill_na:
        csv_file = open(f"tweets_scrape_{CRYPTO}_filled_na.csv", "w",
                        newline = "", encoding = "utf-16")
    else:
        csv_file = open(f"tweets_scrape_{CRYPTO}.csv", "w", newline = "",
                        encoding = "utf-16")
    # Create the csv file to record requested information    
    wtr = csv.writer(csv_file, delimiter = "\t")
    wtr.writerow(["User_Name", "Time_Stamp", "Content", "Sentiment", "Angry",
                  "Fear", "Happy", "Sad", "Surprise", "Num_Reply", "Num_Like"])
    for post in posts:
        # Get the header section of one specific post
        header = post.find("div", class_ = HEADER_CLASS)
        # Get the user's name
        user_name = header.find("a", class_ = USER_NAME_CLASS).span.text
        # Get the user's market sentiment: bullish or bearish
        try:
            sentiment = header.find("div", class_ = SENTIMENT_CLASS).text
        except:
            sentiment = None
        # Get the post's time stamp
        time_s = header.find("a", class_ = TIME_STAMP_CLASS).text
        # Adjust the format of time stamp
        if time_s == "now":
            time_s = NOW.strftime(TIME_FORMAT)
        elif time_s[-1] == "m":
            time_s =  NOW - datetime.timedelta(minutes = int(time_s[:-1]))
            time_s = time_s.strftime(TIME_FORMAT)
        elif len(time_s) == 8:
            h_m = datetime.datetime.strptime(time_s, "%I:%M %p").time()
            time_s = datetime.datetime.combine(datetime.date.today(), h_m)
            time_s = time_s.strftime(TIME_FORMAT)
        else:
            time_s = datetime.datetime.strptime(time_s, "%m/%d/%y, %I:%M %p")
            time_s = time_s.strftime(TIME_FORMAT)
        # Get the post's main text and try to extract emotion from posts, fill
        # empty bull/bear tags if requested
        try:
            content = post.find("div", class_ = CONTENT_CLASS).text
            emotions = te.get_emotion(content)
            if sentiment == None and fill_na:
                vector = np.array([emotions["Angry"], emotions["Fear"],
                                   emotions["Happy"], emotions["Sad"],
                                   emotions["Surprise"]])
                if classifier.predict(vector.reshape(1, -1))[0] == 1:
                    sentiment = "Bullish"
                else:
                    sentiment = "Bearish"
        except:
            content = None
            emotions = {"Angry": None, "Fear": None, "Happy": None,
                        "Sad": None, "Surprise": None}
        # Get the post's reply number and like number to measure its impact
        try:
            reply_div = post.find("div", title = "Reply")
            reply_num = int(reply_div.find("span", class_ = RATE_CLASS).text)
        except:
            reply_num = 0
        try:
            like_div = post.find("div", title = "Like")
            like_num = int(like_div.find("span", class_ = RATE_CLASS).text)
        except:
            like_num = 0
        # Record parsed information of one specific post to the csv file
        wtr.writerow([user_name, time_s, content, sentiment, emotions["Angry"],
                      emotions["Fear"], emotions["Happy"], emotions["Sad"],
                      emotions["Surprise"], reply_num, like_num])
    csv_file.close()

def main():
    print("### 1. Scrape tweets on Stocktwits and generate an html file\n")
    html_is_exist = os.path.exists("tweets_scrape_ETH.X.html")
    if html_is_exist:
        print("## Requirement already satisfied: Local file exists\n")
    if not html_is_exist:
        get_html(num_scroll = 150)
        print("## HTML file created successfully\n")
    print()
    print("### 2. Fit Logistic Regression on bull/bear tags on database.csv\n")
    score, clf = predict_sentimet(database = CWD + "/tweets_database.csv")
    print("## Report model's performance of fitting\n")
    print(f"# Purity Ratio: {score}")
    print("\n")
    print("### 3. Parse the scraped HTML file, generate tweets_scrape.csv"\
          " file and tweets_scrape_filled_na.csv file\n")
    parse_html(clf, fill_na = False, limit = 1000)
    parse_html(clf, fill_na = True, limit = 1000)
    print("## Complete")


if __name__ == "__main__":
    main()
