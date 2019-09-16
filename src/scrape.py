import requests
from src.definitions import PROXIES, EMPIRE_MARKET_URL
from lxml import html
from bs4 import BeautifulSoup

def login_and_set_cookie():
    return {
        'ab': "1cc735432450e28fa3333f2904cd5ae3",
        'shop': "bic414edjoivi8in4q9profsfd9alvhj"
    }

cookies = login_and_set_cookie()

headers = {
    "Host": "empiremktxgjovhm.onion",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "http://empiremktxgjovhm.onion/login",
    "Cookie": "ab="+cookies['ab']+";shop="+cookies['shop']+";",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


for pagenr in range(1, 2249):
    url = "http://"+EMPIRE_MARKET_URL+"/category/categories/2/" + str((pagenr-1)*15)
    res = requests.get(url, proxies=PROXIES, headers=headers).content.decode('utf-8')
    soup = BeautifulSoup(res)
    td = soup.body.padp
    pass