import os

DEBUG_MODE = False

TOR_PORT = 9050

PROXIES = {
    'http': "socks5h://localhost:{}".format(TOR_PORT),
    'https': "socks5h://localhost:{}".format(TOR_PORT)
}

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
WORKING_DIR = os.getcwd() + "/"
DB_ENGINE_URL = 'mysql+mysqlconnector://msc-scraper:Password123!@localhost:3306/scraping'
DB_CLIENT_ENCODING = "utf8"
MYSQL_TEXT_COLUMN_MAX_LENGTH = 65535

ANTI_CAPTCHA_ACCOUNT_KEY = "6c5815eb3db205d9c4a05ba6941b0a3a"
ANTI_CAPTCHA_CREATE_TASK_URL = "http://api.anti-captcha.com/createTask"
ANTI_CAPTCHA_GET_TASK_URL = "https://api.anti-captcha.com/getTaskResult "
ANTI_CAPTCHA_WAIT_INTERVAL = 2
ANTI_CAPTCHA_INITIAL_WAIT_INTERVAL = 6

#EMPIRE MARKET
EMPIRE_MARKET_URL = "empiremktxgjovhm.onion"
EMPIRE_MARKET_CREDENTIALS = [["using_python3", "Password123!"],
                            ["using_python4", "Password123!"],
                             ["using_python5", "Password123!"]]

EMPIRE_MARKET_LOGIN_URL = "http://" + EMPIRE_MARKET_URL + "/index/login"
EMPIRE_MARKET_HOME_URL = "http://" + EMPIRE_MARKET_URL + "/home"
EMPIRE_IMAGE_CAPTCHA_URL_REGEX = r"http:\/\/"+EMPIRE_MARKET_URL.replace(".", "\.")+"\/public\/captchaimg\/[0-9]{10}\.[0-9]{3}\.jpg"
EMPIRE_BASE_CRAWLING_URL = "http://" + EMPIRE_MARKET_URL + "/category/categories/2/"
EMPIRE_MARKET_ID = "EMPIRE_MARKET"
EMPIRE_DIR = ROOT_DIR + "src/empire/"


