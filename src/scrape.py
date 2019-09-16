import requests

EMPIRE_MARKET_URL = "empiremktxgjovhm.onion"
IMAGE_CAPTCHA_URL_REGEX = r"http:\/\/"+EMPIRE_MARKET_URL.replace(".", "\.")+"\/public\/captchaimg\/[0-9]{10}\.[0-9]{3}\.jpg"
TOR_PORT = 9050

PROXIES = {
    'http': "socks5h://localhost:{}".format(TOR_PORT),
    'https': "socks5h://localhost:{}".format(TOR_PORT)
}

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
    url = "http://empiremktxgjovhm.onion/category/categories/2/" + str((pagenr-1)*15)
    #url = "https://vg.no"
    res = requests.get(url, proxies=PROXIES, headers=headers).content.decode('UTF-8')
    print(res)
