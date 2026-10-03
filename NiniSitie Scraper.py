""" WARNING: 
Webscraping may be illegal. please check your country rules before doing that!!!
__author__ = 'Pedram Porbaha'
__email__ = 'p.porbaha@gmail.com'
__date__ = '2026'
"""

import pandas as pd
from selenium import webdriver
from chromedriver_py import binary_path
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.chrome.service import Service

import socket
import time
from random import randint, choice
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
from datetime import datetime
import os
import json
import traceback

# %%
os.makedirs('Result_NiniSite_Scrape', exist_ok=True)

service = Service(executable_path=binary_path)
driver = webdriver.Chrome(service=service)
driver.maximize_window()

driver.get('https://www.ninisite.com/Imen/SignIn')
print('After signing in in ninisite, please press ENTER (your phone number and password)')
# %%

sep = '\t|\t'


def write_initial():
    os.makedirs(r'Result_NiniSite_Scrape\ninisite_comments', exist_ok=True)

    with open(r'Result_NiniSite_Scrape\comments.txt', 'w', encoding='utf-8', errors='ignore') as f:
        f.write('idx' + '\t' + 'Symbol' + '\t' + 'ArticleCounts')
        f.write('\n')


def wait_for_internet(interval=5):
    """Wait until internet connection is available"""

    dns_servers = [
        ("8.8.8.8", 53),
        ("8.8.4.4", 53),
        ("1.1.1.1", 53),
        ("1.0.0.1", 53),
        ("4.2.2.4", 53),
        ("208.67.222.222", 53),
        ("208.67.220.220", 53),
        ("9.9.9.9", 53),
        ("149.112.112.112", 53),
        ("94.140.14.14", 53),
    ]

    while True:
        host, port = choice(dns_servers)

        try:
            socket.setdefaulttimeout(3)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            break  # Internet connected, exit the loop
        except socket.error:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ Offline (tried {host})")

        time.sleep(interval)


def find(path):
    return driver.find_element('css selector', path)


def finds(path):
    return driver.find_elements('css selector', path)


def search_item(search_term):
    base_url = f'https://www.ninisite.com/search/discussion?q={search_term}&f=1'

    wait_for_internet()
    driver.get(base_url)

    path = '.pagination li'
    elems = finds(path)
    if elems:
        page_counts = int(elems[-2].text)
    else:
        page_counts = 1
    return page_counts


def extract_topic_links_on_each_page(search_term, page_num):
    url = f'https://www.ninisite.com/search/discussion?q={search_term}&f=1&page={page_num}'
    wait_for_internet()
    driver.get(url)
    path = 'div.col-xs-12.col-lg-10 a'
    elems = finds(path)
    topics_on_page = [(elem.text, elem.get_attribute('href')) for elem in elems]
    return topics_on_page


def all_topics_extractor():
    search_term = 'سرما خورد'  # dont be a perfectinist! :)
    page_counts = search_item(search_term)
    topics_total = {}
    topics_total[search_term] = []
    for page_num in range(1, page_counts):
        print(f'{page_num=}')
        topics_on_page = extract_topic_links_on_each_page(search_term, page_num=page_num)
        topics_total[search_term].extend(topics_on_page)  # Each page has 20 topics

    with open(r'Result_NiniSite_Scrape\topics_links.json', mode='w') as f:
        json.dump(topics_total, f)


def remove_just_cold_word(topics_total):
    for item in topics_total['سرما خورد']:
        topic, link = item
        if topic == 'سرما':  # irrelevant to sickness
            topics_total['سرما خورد'].remove(item)
        return topics_total


def extract_page_count_in_each_topic():
    path = '.pagination li'
    elems = finds(path)
    if elems:
        page_counts = int(elems[-2].text)
    else:
        page_counts = 1
    return page_counts


def extract_starting_date_of_topic():
    path = '.topic-post .date'
    elem = find(path)
    date = elem.text
    return date


def extract_comment_from_one_page_each_topic(link, page_num):
    url = link + f'?page={page_num}'
    driver.get(url)

    path = '.topic-post .post-message'
    comments = [elem.text for elem in finds(path)]

    path = '.topic-post .user-info'
    users = [elem.text for elem in finds(path)]

    path = '.topic-post .nickname'
    names = [elem.text for elem in finds(path)]

    comments_in_one_page = []
    for name, user, comment in zip(names, users, comments):
        if 'استارتر' in user:
            is_starter = True
        else:
            is_starter = False

        if 'عضویت' not in user:
            is_advertising = True
        else:
            is_advertising = False

        comments_in_one_page.append({
            'name': name,
            'user': user,
            'is_starter': is_starter,
            'is_advertising': is_advertising,
            'comment': comment
        })
    return comments_in_one_page


def extract_all_comments_from_topic(topic, link):
    topic_all_comments = []

    driver.get(link)
    page_counts = extract_page_count_in_each_topic()
    starting_date_of_topic = extract_starting_date_of_topic()

    for page_num in range(1, page_counts + 1):
        comments_from_one_page = extract_comment_from_one_page_each_topic(link, page_num)
        topic_all_comments.extend(comments_from_one_page)

    return topic_all_comments, starting_date_of_topic

def excel_file_from_all_comments(topic_comments):
    all_comments = []
    for topic in topic_comments:
        topic_name = topic['topic']
        link = topic['link']
        start_date = topic['start_date']
        topic_is_relevant = topic['is_relevant']
        topic_relevancy_reason = topic['reason_for_relevancy']

        for idx, each_comment in enumerate(topic['topic_comments']):
            if idx == 0:
                starting_comment = each_comment['comment']


            comment = each_comment['comment']
            is_starter = each_comment['is_starter']
            is_advertising = each_comment['is_advertising']
            user_name = each_comment['name']

            if is_advertising:
                continue

            all_comments.append({
                'topic': topic_name,
                'topic_is_relevant':topic_is_relevant,
                'topic_relevancy_reason':topic_relevancy_reason,
                'topic_start_date':start_date,
                'topic_link': link,
                'user_name': user_name,
                'is_starter': is_starter,
                # 'is_advertising': is_advertising,
                'comment': comment
            })

    df = pd.DataFrame(all_comments)
    df.to_excel(r'Result_NiniSite_Scrape\topics_comments.xlsx')
    return df

# %%
search_term = 'سرما خورد'

# topics_total = all_topics_extractor()
with open(r'Result_NiniSite_Scrape\topics_links.json', mode='r') as f:
    topics_total = json.load(f)

# in this function I just return the  topics_total['سرما خورد'] instead of topics_total
topics_total = remove_just_cold_word(topics_total)

#
# # Extracting comments
# all_topic_comments = []
# topic_counts = len(topics_total[search_term])
# # until 2120
# for idx, (topic, link) in enumerate(topics_total[search_term][:2120]):
#     print(f'{idx} from {topic_counts}')
#     print(topic)
#
#     try:
#         wait_for_internet()
#         topic_comments, starting_date_of_topic = extract_all_comments_from_topic(topic, link)
#         all_topic_comments.append({
#             'topic':topic,
#             'start_date':starting_date_of_topic,
#             'link': link,
#             'topic_comments':topic_comments
#         })
#
#     except Exception:
#         error = str(traceback.format_exc())
#         print(error)
#
# with open(r'Result_NiniSite_Scrape\topics_comments.json', mode='w') as f:
#     json.dump(all_topic_comments, f)

with open(r'Result_NiniSite_Scrape\topics_comments_with_relevancy_column.json') as f:
    topic_comments = json.load(f)

df = excel_file_from_all_comments(topic_comments)



