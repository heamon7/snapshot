# coding: utf-8
import leancloud
from leancloud import Engine
from leancloud import LeanEngineError

from app import app


import requests

import os
import json
import logging
import time

import pandas as pd
import tushare as ts

import collections

from logentries import LogentriesHandler
import logging as log

import requests
import logging
import re
import time
from urllib.parse import quote
import random

from scrapy.selector import Selector
from scrapy.http import HtmlResponse
import json
from pandas.io.json import json_normalize


engine = Engine(app)

WEIXIN_URL = 'http://mp.weixin.qq.com/profile?src=3&timestamp={}&ver=1&signature={}'
BASE_URL = 'http://weixin.sogou.com'


UA = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"



def get_html(url):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        UA
    )
    dcap["takesScreenshot"] = (False)
    #t0 = time.time()
    try:
        driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=['--load-images=no'])
        driver.set_page_load_timeout(240)
        driver.command_executor._commands['executePhantomScript'] = ('POST', '/session/$sessionId/phantom/execute')

        driver.execute('executePhantomScript', {'script': '''
            var page = this; // won't work otherwise
            page.onResourceRequested = function(requestData, request) {
                if ((/http:\/\/.+?\.css/gi).test(requestData['url']) || requestData['Content-Type'] == 'text/css') {
                    console.log('The url of the request is matching. Aborting: ' + requestData['url']);
                    request.abort();
                }
            }
            ''', 'args': []})
    except selenium.common.exceptions.WebDriverException:
        return None
    try:
        driver.get(url)
        html = driver.page_source
    except Exception as e:
        html = None
        logging.error(e)
    finally:
        driver.quit()
    return html

def get_html_direct(url,cookies=None):
    if not cookies:
        cookies = update_cookies()
    headers = {"User-Agent": UA}
    r = requests.get(url, headers=headers, cookies=cookies, timeout=20)
    return r.text

def get_account_info(weixinhao=None, link=None, cookies=None):
    url = 'http://weixin.sogou.com/weixin?type=1&s_from=input&query={}&ie=utf8&_sug_=n&_sug_type_='.format(weixinhao)
    res = get_html_direct(url)
    sel = Selector(text= res)
    signature_url = sel.xpath("//div[contains(@class,'img-box')]/a/@href").extract()[0]
    img_url = sel.xpath("//div[contains(@class,'img-box')]/a/img/@src").extract()[0]
    weixin_name = sel.xpath("//div[contains(@class,'txt-box')]//a/text()").extract()[0]
    description = sel.xpath("//dl/dd/text()").extract()[0]
    # qr_code = sel.xpath("//span[contains(@class,'pop')]/img/@src").extract()[0]
    return signature_url

def get_msg_list(signature_url=None):
    res = get_html_direct(signature_url)
    if not res:
        return None
    res = get_html_direct(url)
    sel = Selector(text= res)
    weixinhao = sel.xpath("//p[contains(@class,'profile_account')]/text()").extract()[0].split(u': ')[1]
    msg_list = json.loads(res.split('var msgList = ')[1].split(';\r\n        seajs.use(')[0])['list']
    pd_msg = json_normalize(msg_list)
    msg_list = json.loads(pd_msg.to_json(orient='records'))
    return msg_list
    # for msg in msg_list:


def parse_essay(link):
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    try:
        r = s.get(link)
        html = r.text
        soup = BeautifulSoup(html)
        essay = {}
        p = re.compile(r'\?wx_fmt.+?\"')
        content = str(soup.select("#js_content")[0]).replace('data-src', 'src')
        essay['content'] = re.sub(p, '"', content)
        essay['name'] = soup.select('#post-user')[0].text
        essay['date'] = soup.select('#post-date')[0].text
    except Exception:
        return None

    return essay


def weixin_search(name, cookies=None):
    url = BASE_URL + '/weixin?query=' + name
    #html = get_html(url)
    html = get_html_direct(url, cookies=cookies)
    print(html)
    soup = BeautifulSoup(html)
    ls = soup.select("._item")
    search_list = []
    for item in ls:
        account_info = {}
        account_info['account'] = item.select('h4 span')[0].text.split('：')[1].strip()
        account_info['name'] = item.select('.txt-box h3')[0].text
        account_info['address'] = BASE_URL + item['href']
        account_info['open_id'] = item['href'].split('openid=')[1]
        account_info['description'] = item.select('.sp-txt')[0].text
        account_info['logo'] = item.select('.img-box img')[0]['src']
        try:
            account_info['latest_title'] = item.select('.sp-txt a')[0].text
            account_info['latest_link'] = item.select('.sp-txt a')[0]['href']
        except IndexError:
            pass
        search_list.append(account_info)
        #print(account_info)
    return search_list

def get_signature(weixinhao):
    url = 'http://weixin.sogou.com/weixin?type=1&s_from=input&query={}&ie=utf8&_sug_=n&_sug_type_='.format(weixinhao)
    res = get_html_direct(url)
    sel = Selector(text= res)
    signature_url = sel.xpath("//div[contains(@class,'img-box')]/a/@href").extract()[0]    
    return signature_url

def update_cookies():
    s = requests.Session()
    headers = {"User-Agent": UA}
    s.headers.update(headers)
    url = BASE_URL + '/weixin?query=123'
    r = s.get(url)
    if 'SNUID' not in s.cookies:
        p = re.compile(r'(?<=SNUID=)\w+')
        s.cookies['SNUID'] = p.findall(r.text)[0]
        suv = ''.join([str(int(time.time()*1000000) + random.randint(0, 1000))])
        s.cookies['SUV'] = suv
    return s.cookies















