import os

from sqlalchemy.ext.declarative import declarative_base

from environmentSettings import MYSQL_ECHO_DEBUG

ONE_WEEK = 3600*24*7

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
WORKING_DIR = os.getcwd() + "/"

MYSQL_TEXT_COLUMN_MAX_LENGTH = 65435
MYSQL_MEDIUM_TEXT_COLUMN_MAX_LENGTH = 16770215
MYSQL_CASCADE = "CASCADE"
MYSQL_URL_PARAMS = {"charset": "utf8"}
MYSQL_URL_PARAMS_STRING = "?".join([''] + [(key + "=" + MYSQL_URL_PARAMS[key]) for key in MYSQL_URL_PARAMS.keys()])
MYSQL_CONNECT_ARGS = {'buffered': True,
                        'collation': 'utf8mb4_general_ci',
                      'charset': "utf8mb4"}
SQLALCHEMY_CREATE_ENGINE_KWARGS = {'encoding': 'utf-8',
                                   'echo': MYSQL_ECHO_DEBUG,
                                   'connect_args': MYSQL_CONNECT_ARGS}

DBMS_DISCONNECT_RETRY_INTERVALS = [5, 5, 5, 5, 5, 5, 5, 100]
ERROR_FINGER_PRINT_COLUMN_LENGTH = 4
FEEDBACK_TEXT_HASH_COLUMN_LENGTH = 8
FEEDBACK_BUYER_COLUMN_LENGTH = 5
URL_COLUMN_LENGTH = 80
SELLER_NAME_COLUMN_LENGTH = 32
COUNTRY_NAME_COLUMN_LENGTH = 56 # The United Kingdom of Great Britain and Northern Ireland
MARKET_NAME_COLUMN_LENGTH = 32
FEEDBACK_CATEGORY_COLUMN_LENGTH = 20
CURRENCY_COLUMN_LENGTH = 3

MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD = 40
CREATED_DATE_COLUMN_NAME = "created_date"

ANTI_CAPTCHA_ACCOUNT_KEY = "6c5815eb3db205d9c4a05ba6941b0a3a"
ANTI_CAPTCHA_CREATE_TASK_URL = "http://api.anti-captcha.com/createTask"
ANTI_CAPTCHA_GET_TASK_URL = "https://api.anti-captcha.com/getTaskResult"
ANTI_CAPTCHA_WAIT_INTERVAL = 2
ANTI_CAPTCHA_INITIAL_WAIT_INTERVAL = 6

#EMPIRE MARKET
EMPIRE_MARKET_URL = "empiremktxgjovhm.onion"
EMPIRE_MARKET_CREDENTIALS = [["using_python3", "Password123!"],
                             ["using_python4", "Password123!"],
                             ["using_python5", "Password123!"],
                             ["using_python6", "Password123!"],
                             ["using_python7", "Password123!"],
                             ["using_python8", "Password123!"],
                             ["using_python9", "Password123!"],
                             ["using_python10", "Password123!"]]

RESCRAPE_PGP_KEY_INTERVAL = ONE_WEEK
EMPIRE_MARKET_LOGIN_URL = "http://" + EMPIRE_MARKET_URL + "/index/login"
EMPIRE_MARKET_HOME_URL = "http://" + EMPIRE_MARKET_URL + "/home"
EMPIRE_IMAGE_CAPTCHA_URL_REGEX = r"http:\/\/"+EMPIRE_MARKET_URL.replace(".", "\.")+"\/public\/captchaimg\/[0-9]{10}\.[0-9]{3}\.jpg"
EMPIRE_BASE_CATEGORY_URL = "http://" + EMPIRE_MARKET_URL + "/category/"
EMPIRE_MARKET_ID = "EMPIRE_MARKET"
EMPIRE_DIR = ROOT_DIR + "src/empire/"
EMPIRE_HTTP_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

Base = declarative_base()