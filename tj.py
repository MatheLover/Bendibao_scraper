import re
import sys
from random import randint
import pandas as pd
import requests
from bs4 import BeautifulSoup
from time import sleep
import logging

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')

# base url for each article given each city
url_1 = 'http://m.tj.bendibao.com/'

# url of first page on covid-19 policy given the city
url_2 = 'http://m.tj.bendibao.com/news/tianjindongtai/'

# base url given the city for turning pages
url_3 = 'http://m.tj.bendibao.com/news/tianjindongtai/'
table_elem_list = []


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
    year = article_time[0:4]

    # if year is less than 2020, exit
    if int(year) < 2020:
        sys.exit()

    # article texts
    article_content = result.find_all("div", class_="content-box")
    article_text = ""
    # find all p tags
    p_tag_list = article_content[0].find_all("p")
    for d in p_tag_list:
        if d.find('table') is None:
            article_text += (d.text.strip())

    # article table
    table = result.find('table')
    if table is not None:
        rows = None
        if table is not None:
            rows = table.find_all('tr')
        if rows is not None:
            first = rows[0]
            allRows = rows[1:-1]
            escapes = ''.join([chr(char) for char in range(1, 32)])
            translator = str.maketrans('', '', escapes)
            headers = [header.get_text().strip() for header in first.find_all('td')]
            test = [[data.get_text().translate(translator) for data in row.find_all('td')] for row in allRows]

            rowspan = []

            for no, tr in enumerate(allRows):
                for td_no, data in enumerate(tr.find_all('td')):
                    if data.get("rowspan") is not None:
                        t = data.get_text()
                        escapes = ''.join([chr(char) for char in range(1, 32)])
                        translator = str.maketrans('', '', escapes)
                        t = t.translate(translator)
                        rowspan.append((no, td_no, int(data["rowspan"]), t))
            if rowspan:
                for i in rowspan:
                    # i[0], i[1], i[2], i[3] -- row index involving repetitive data (non-header rows), row index td with row span,number of repetitions  ,repetitive data
                    # tr value of rowspan in present in 1th place in results
                    for j in range(1, i[2]):
                        # - Add value in next tr.
                        test[i[0] + j].insert(i[1], i[3])

        # create df for tables
        df = pd.DataFrame(data=test, columns=headers)
        df = df.to_string()

    # concatenate articles and tables
    if 'df' in locals():
        article_text = article_text + '\n\n' + df

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

    df.to_csv('test.csv', index=False, header=False)

    # try to call next page
    page_turner = soup.find_all("a", string=">")
    while len(page_turner[0]['href']) != 0:
        URL = url_3 + page_turner[0]['href']

        # logging page number
        logging.info("Processing page: %s", URL)

        sleep(randint(10, 15))
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
            new_row.to_csv('test.csv', mode='a', index=False, header=False)
        page_turner = soup.find_all("a", string=">")
