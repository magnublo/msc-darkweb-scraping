import os

DEBUG_MODE = False

TOR_PORT = 9050

PROXIES = {
    'http': "socks5h://localhost:{}".format(TOR_PORT),
    'https': "socks5h://localhost:{}".format(TOR_PORT)
}

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
WORKING_DIR = os.getcwd() + "/"
DB_ENGINE_URL = 'postgresql://postgres:Password123!@localhost:5432/scraping'
DB_CLIENT_ENCODING = "utf8"

#EMPIRE MARKET
EMPIRE_MARKET_URL = "empiremktxgjovhm.onion"
EMPIRE_MARKET_LOGIN_URL = "http://" + EMPIRE_MARKET_URL + "/index/login"
EMPIRE_IMAGE_CAPTCHA_URL_REGEX = r"http:\/\/"+EMPIRE_MARKET_URL.replace(".", "\.")+"\/public\/captchaimg\/[0-9]{10}\.[0-9]{3}\.jpg"
EMPIRE_BASE_CRAWLING_URL = "http://" + EMPIRE_MARKET_URL + "/category/categories/2/"
EMPIRE_MARKET_ID = "EMPIRE_MARKET"
EMPIRE_DIR = ROOT_DIR + "src/empire/"


