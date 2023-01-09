'''
    Crypto_Prices_Predicting_Project
    Summer 2022

    Scrape text from the last 25 articles using the keyword
    "cryptocurrency" on WSJ and record information as a csv file

    Hongyan Yang
'''


import csv
import time
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

TIME_FORMAT = "%m/%d/%Y, %H:%M:%S"

URL = "https://www.wsj.com/search?query=cryptocurrency&isToggleOn=true&" \
      "operator=AND&sort=date-desc&duration=4y&startDate=2018%2F07%2F02&" \
      "endDate=2022%2F07%2F02&source=wsjie%2Cblog%2Cinteractivemedia" \
      "%2Cwsjsitesrch%2Cwsjpro%2Cwsjaudio"
USERNAME = "fonzieyang@brandeis.edu"
PASSWORD = "759153Wa!"
PROCEED_BUTTON = ".//button[@type='button']" \
                 "[@class='solid-button continue-submit new-design']"
SUBMIT_BUTTON = ".//button[@type='submit']" \
                "[@class='solid-button new-design basic-login-submit']"

INFO_CLASS = "WSJTheme--search-text-combined--29JN8aap"
TITLE_CLASS = "WSJTheme--headlineText--He1ANr9C"
TIME_CLASS = "WSJTheme--timestamp--2zjbypGD"
AUTHOR_CLASS = "WSJTheme--byline--1oIUvtQ3"

PARAGRAPH_CLASS = "Paragraph-sc-u5wzz1-0 cStoSw"
CONTENT_CLASS_0 = "ArticleBody__Container-sc-1h79tj2-0 eijvTq"
CONTENT_CLASS_1 = "article-content"
CONTENT_CLASS_2 = "WSJTheme--player--1m1cgHQM"
CONTENT_CLASS_3 = "article_content"

locate_item = EC.presence_of_element_located
locate_items = EC.presence_of_all_elements_located
click_item = EC.element_to_be_clickable

def wsj_login(driver, url = URL):
    '''
    Apply selenium methods to auto login the WSJ website
    '''
    wait = WebDriverWait(driver, 10)
    driver.get(url) # Visit the WSJ website
    time.sleep(3)
    # Click the sign in button
    wait.until(locate_item((By.LINK_TEXT, "Sign In"))).click()
    time.sleep(1)
    # Enter the username and proceed
    wait.until(click_item((By.ID, "username"))).send_keys(USERNAME)
    wait.until(locate_item((By.XPATH, PROCEED_BUTTON))).click()
    time.sleep(1)
    # Enter the password and submit, return to the original page
    wait.until(click_item((By.ID,
                           "password-login-password"))).send_keys(PASSWORD)
    wait.until(locate_item((By.XPATH, SUBMIT_BUTTON))).click()
    time.sleep(3)

def parse_info(html_file):
    '''
    Parse the scraped html file to get the info of the article including title,
    links, authers and time stamps
    '''
    doc = BeautifulSoup(html_file, "lxml")
    info_sections = doc.find_all("div", class_ = INFO_CLASS)
    # Get articles' titles
    titles = [s.find("span", class_ = TITLE_CLASS).text for s in info_sections]
    links = [section.a["href"] for section in info_sections]    # Get links
    # Get articles' authors info
    authors = []       
    for section in info_sections:
        try:
            a = section.find("p", class_ = AUTHOR_CLASS).text
            a = a.replace(" and", ",").strip()
            authors.append(a)
        except:
            authors.append(None)
    # Get articles' time stamps info
    times = []
    for section in info_sections:
        try:
            t = section.find("div", class_ = TIME_CLASS)
            t = datetime.datetime.strptime(t.p.text[:-3], "%B %d, %Y %I:%M %p")
            t = t.strftime(TIME_FORMAT)
            times.append(t)
        except:
            times.append(None)
    return titles, links, authors, times

def parse_content(html_file, type = 0):
    '''
    Parse the scraped html file to get the content of the article
    '''
    # Parse the html file with BeautifulSoup
    article = BeautifulSoup(html_file, "lxml")
    if type == 0:
        # Get articles's content
        content_section = article.find("section", class_ = CONTENT_CLASS_0)
        paragraphs = content_section.find_all("p", class_ = PARAGRAPH_CLASS)
        content = ""
        for paragraph in paragraphs:
            content += (paragraph.text + "\n")
    elif type == 1:
        content_section = article.find("div", class_ = CONTENT_CLASS_1)
        paragraphs = content_section.find_all("p")
        content = ""
        for paragraph in paragraphs:
            content += (paragraph.text + "\n")
    elif type == 2:
        content_section = article.find("div", class_ = CONTENT_CLASS_2)
        paragraphs = content_section.find_all("p")
        content = ""
        for paragraph in paragraphs:
            content += (paragraph.text + "\n")
    else:
        content_section = article.find("div", class_ = CONTENT_CLASS_3)
        paragraphs = content_section.find_all("p")
        content = ""
        for paragraph in paragraphs:
            content += (paragraph.text + "\n")
    return content

def wsj_scrape(articles_num = 25):
    '''
    Auto login to the WSJ website and scrape required number of articles with
    given url
    Create a csv file to record each article's title, link, author, time stamp
    and content
    '''
    chrome_driver = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = chrome_driver)
    wait = WebDriverWait(driver, 10)
    # Create a csv file to record required information
    csv_file = open("wsj_scrape.csv", "w", newline = "", encoding = "utf-16")
    wtr = csv.writer(csv_file, delimiter = "\t")
    wtr.writerow(["Title", "Link", "Author(s)", "Time_Stamp", "Content"])
    count, parsed_count, page_num = 0, 0, 1
    # Auto login to the WSJ website
    wsj_login(driver, url = URL)
    # Keep scrapping until parsing required number of articles
    while count < articles_num:
        time.sleep(3)
        driver.get(URL + "&page=" + str(page_num))
        time.sleep(3)
        html_file = driver.page_source
        time.sleep(1)
        # Parse article's title, link, author, time stamp information
        titles, links, authors, times = parse_info(html_file)
        i = 0
        while i < min(len(titles), (articles_num - parsed_count)):
            try:
                time.sleep(2)
                wait.until(locate_item((By.LINK_TEXT, titles[i]))).click()
                time.sleep(1)
                # Parse article's content
                html_file = driver.page_source
                time.sleep(3)
            except:
                driver.refresh()
            for j in range(4):
                try:
                    content = parse_content(html_file, type = j)
                    print(f"ARTICLE {count + 1}:\n")
                    print(titles[i])
                    print()
                    print(content[:500])
                    print("\n********************************************\n")
                    wtr.writerow([titles[i], links[i], authors[i], times[i],
                                  content])
                    content = None
                    i += 1
                    count += 1
                    driver.back()
                    time.sleep(3)
                    break
                except:
                    continue
        page_num += 1
        parsed_count = count
    csv_file.close()

def main():
    wsj_scrape(articles_num = 25)


if __name__ == "__main__":
    main()
