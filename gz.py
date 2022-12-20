from random import randint
import pandas as pd
import requests
from bs4 import BeautifulSoup
from time import sleep
import logging
logging.basicConfig(level="INFO")

# base url for each article given each city
url_1 = 'http://m.gz.bendibao.com/'

# url of first page on covid-19 policy given the city
url_2 = 'http://m.gz.bendibao.com/news/list_17_176_1.htm'

# base url given the city for turning pages
url_3 = 'http://m.gz.bendibao.com/news/'


def article_parsing(url):
    # result parsing
    # 'http://m.xa.bendibao.com/news/108227.shtm'
    content = requests.get(url)
    content.encoding = content.apparent_encoding
    result = BeautifulSoup(content.text, "html.parser")

    # article title
    title = result.find("h1").get_text()

    # article time
    article_time = result.find("span", class_="public_time").get_text()

    # article texts
    article_content = result.find_all("div", class_="content-box")
    article_text = ""
    for d in article_content[0].find_all("p"):
        article_text += (d.text.strip())

    return article_time, title, article_text


def article_url(div_tag_list):
    url_list = []
    # list of items within a page
    for div in div_tag_list:
        a = div.find_all("a", {"target": "_blank"})
        url_list.append(url_1 + a[0]['href'])
    return url_list


if __name__ == "__main__":
    # create empty dataframe
    df = pd.DataFrame(columns=['Time', 'Title', 'Content'])

    # start with initial page
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
    r = requests.get(url_2)
    soup = BeautifulSoup(r.text, "html.parser")

    # logging page url
    logging.info("Processing page: %s", url_2)

    div_tag_list = soup.find_all("div", class_="list-item2016")

    # get url of each result within the page
    url_list = article_url(div_tag_list)
    for url in url_list:
        article_time, title, article_text = article_parsing(url)

        # append new row to the dataframe
        new_row = {'Time': article_time, 'Title': title, 'Content': article_text}
        new_row = pd.DataFrame.from_records([new_row])
        df = pd.concat([df, new_row])
        df.to_csv('test.csv', mode='a', index=False, header=False)

    # try to call next page
    page_turner = soup.find_all("a", string=">")
    while len(page_turner[0]['href']) != 0:
        URL = url_3 + page_turner[0]['href']

        # logging page number
        logging.info("Processing page: %s",URL)

        sleep(randint(180,200))
        r = requests.get(URL, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        div_tag_list = soup.find_all("div", class_="list-item2016")
        url_list = article_url(div_tag_list)
        for url in url_list:
            article_parsing(url)
            article_time, title, article_text = article_parsing(url)

            # append new row to the dataframe
            new_row = {'Time': article_time, 'Title': title, 'Content': article_text}
            new_row = pd.DataFrame.from_records([new_row])
            df = pd.concat([df, new_row])
            df.to_csv('test.csv', mode='a', index=False, header=False)
        page_turner = soup.find_all("a", string=">")
