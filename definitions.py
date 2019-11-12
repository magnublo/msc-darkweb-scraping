import os
from _mysql_connector import MySQLError

from typing import Tuple, List

import requests
import urllib3
from sqlalchemy.exc import SQLAlchemyError, DatabaseError

from sqlalchemy.ext.declarative import declarative_base

from environment_settings import MYSQL_ECHO_DEBUG
from src.exceptions import DeadMirrorException

ONE_WEEK = 3600*24*7
ONE_DAY = 3600*24
ONE_HOUR = 3600

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
ROOT_SRC_DIR = ROOT_DIR + "src/"
WORKING_DIR = os.getcwd() + "/"

MAX_MARKET_THREADS_PER_PROXY = 4
TOR_PROJECT_URL_FOR_CONFIGURATION_CHECK = "https://check.torproject.org/"
TOR_PROJECT_CORRECT_CONFIGURATION_SUCCESS_MESSAGE = "Congratulations. This browser is configured to use Tor."

MYSQL_VARCHAR_DEFAULT_LENGTH = 255
MYSQL_TEXT_COLUMN_MAX_LENGTH = 65535
MYSQL_MEDIUM_TEXT_COLUMN_MAX_LENGTH = 16777215
MYSQL_CASCADE = "CASCADE"
MYSQL_SET_NULL = "SET NULL"
MYSQL_URL_PARAMS = {"charset": "utf8"}
MYSQL_URL_PARAMS_STRING = "?".join([''] + [(key + "=" + MYSQL_URL_PARAMS[key]) for key in MYSQL_URL_PARAMS.keys()])
MYSQL_CONNECT_ARGS = {'buffered': True,
                        'collation': 'utf8mb4_general_ci',
                      'charset': "utf8mb4"}

PYTHON_SIDE_DB_ENCODING = "utf-8"
SQLALCHEMY_CREATE_ENGINE_KWARGS = {'encoding': PYTHON_SIDE_DB_ENCODING,
                                   'echo': MYSQL_ECHO_DEBUG,
                                   'connect_args': MYSQL_CONNECT_ARGS}

MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD = 20
DBMS_DISCONNECT_RETRY_INTERVALS = [5, 5, 5, 5, 5, 5, 5, 100]

MD5_HASH_STRING_ENCODING = "utf-8"
ERROR_FINGER_PRINT_COLUMN_LENGTH = 4
FEEDBACK_TEXT_HASH_COLUMN_LENGTH = 8
FEEDBACK_BUYER_COLUMN_LENGTH = 5
URL_COLUMN_LENGTH = 80
SELLER_NAME_COLUMN_LENGTH = 32
COUNTRY_NAME_COLUMN_LENGTH = 56 # "The United Kingdom of Great Britain and Northern Ireland"
MARKET_NAME_COLUMN_LENGTH = 32
FEEDBACK_CATEGORY_COLUMN_LENGTH = 20
CURRENCY_COLUMN_LENGTH = 3
XMPP_JABBER_ID_COLUMN_LENGTH = 255 #confirmed max on cryptonia
PRODUCT_TITLE_COLUMN_LENGTH = 128
PRODUCT_CATEGORY_NAME_COLUMN_LENGTH = 40
CREATED_DATE_COLUMN_NAME = "created_date"


BEAUTIFUL_SOUP_HTML_PARSER = "lxml"

ANTI_CAPTCHA_ACCOUNT_KEY = os.getenv('ANTI_CAPTCHA_ACCOUNT_KEY')
assert ANTI_CAPTCHA_ACCOUNT_KEY is not None
ANTI_CAPTCHA_CREATE_TASK_URL = "http://api.anti-captcha.com/createTask"
ANTI_CAPTCHA_GET_TASK_URL = "https://api.anti-captcha.com/getTaskResult"
FAILED_CAPTCHAS_PER_PAUSE = 5
TOO_MANY_FAILED_CAPTCHAS_WAIT_INTERVAL = 180.0
ANTICAPTCHA_ERROR_PER_PAUSE = 10
TOO_MANY_ANTICAPTCHA_ERRORS_WAIT_INTERVAL = 600
WAIT_BETWEEN_ANTI_CAPTCHA_NO_WORKERS_AVAILABLE = 5

#EXTERNAL MARKET IDS
DREAM_MARKET_ID = "DREAM_MARKET"
WALL_STREET_MARKET_ID = "WALL_STREET_MARKET"
NUCLEUS_MARKET_ID = "NUCLEUS_MARKET"
ALPHA_BAY_MARKET_ID = "ALPHA_BAY_MARKET"
CGMC_MARKET_ID = "CGMC_MARKET"
HANSA_MARKET_ID = "HANSA_MARKET"
BLACK_BANK_MARKET_ID = "BLACK_BANK_MARKET"
AGORA_MARKET_ID = "AGORA_MARKET"
BLACK_MARKET_RELOADED_ID = "BLACK_MARKET_RELOADED"
ABRAXAS_MARKET_ID = "ABRAXAS_MARKET"
MIDDLE_EARTH_MARKET_ID = "MIDDLE_EARTH_MARKET"
SAMSARA_MARKET_ID = "SAMSARA_MARKET"

#EMPIRE MARKET
EMPIRE_MARKET_URL = "empiremktxgjovhm.onion"
EMPIRE_MARKET_CREDENTIALS = [["using_python3", "Password123!"],
                             ["using_python4", "Password123!"],
                             ["using_python5", "Password123!"],
                             ["using_python6", "Password123!"],
                             ["using_python7", "Password123!"],
                             ["using_python8", "Password123!"],
                             ["using_python9", "Password123!"],
                             ["using_python10", "Password123!"],
                             ["using_python11", "Password123!"],
                             ["using_python12", "Password123!"],
                             ["using_python13", "Password123!"],
                             ["using_python14", "Password123!"]]

RESCRAPE_PGP_KEY_INTERVAL = ONE_WEEK
EMPIRE_MARKET_CATEGORY_INDEX_URL_PATH = "/home"
EMPIRE_MARKET_ID = "EMPIRE_MARKET"
EMPIRE_MIN_CREDENTIALS_PER_THREAD = 1
EMPIRE_SRC_DIR = ROOT_SRC_DIR + "empire/"
EMPIRE_HTTP_HEADERS = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

EMPIRE_MARKET_LOGIN_PHRASE = "Welcome to Empire Market! Please login to access the marketplace."
EMPIRE_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE = "There is currently nothing to show."

EMPIRE_MARKET_EXTERNAL_MARKET_STRINGS: List[Tuple[str, str]] = [
    (DREAM_MARKET_ID, "Dream Market"),
    (WALL_STREET_MARKET_ID, "Wall Street Market")
]


#CRYPTONIA MARKET
CRYPTONIA_MARKET_ID = "CRYPTONIA_MARKET"
CRYPTONIA_MIN_CREDENTIALS_PER_THREAD = 5
CRYPTONIA_MARKET_CATEGORY_INDEX_URL_PATH = "/products"
CRYPTONIA_MARKET_CREDENTIALS = [["usingPython3", "Password123!"]]
CRYPTONIA_DIR = ROOT_DIR + "src/cryptonia/"
CRYPTONIA_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE = "No products found."
CRYPTONIA_PHYSICAL_LISTING_TYPE_STRING = "Physical Listing"
CRYPTONIA_WORLD_COUNTRY: str = "Worldwide"
CRYPTONIA_MARKET_LOGIN_PHRASE = "Please provide your credentials to continue."
CRYPTONIA_MARKET_SUCCESSFUL_LOGIN_PHRASE = "You have been successfully login."
CRYPTONIA_SRC_DIR = ROOT_SRC_DIR + "cryptonia/"

CRYPTONIA_MARKET_EXTERNAL_MARKET_STRINGS: List[Tuple[str, str]] = [
    (EMPIRE_MARKET_ID, "Empire:"),
    (DREAM_MARKET_ID, "Dream:"),
    (WALL_STREET_MARKET_ID, "Wallstreet:"),
    (NUCLEUS_MARKET_ID, "Nucleus:"),
    (ALPHA_BAY_MARKET_ID, "Alphabay:"),
    (CGMC_MARKET_ID, "CGMC:"),
    (HANSA_MARKET_ID, "Hansa:"),
    (BLACK_BANK_MARKET_ID, "Black Bank:"),
    (AGORA_MARKET_ID, "Agora:"),
    (BLACK_MARKET_RELOADED_ID, "Black Market Reloaded:"),
    (ABRAXAS_MARKET_ID, "Abraxas:"),
    (MIDDLE_EARTH_MARKET_ID, "Middle Earth:")
]


NR_OF_REQUESTS_BETWEEN_PROGRESS_REPORT = 10

DEAD_MIRROR_TIMEOUT = 1200.0  # if mirror has not responded in this many seconds, rotate mirror
MINIMUM_WAIT_TO_RECHECK_DEAD_MIRROR = 1800.0  # a mirror will not be rechecked if it has failed within this many seconds
REFRESH_MIRROR_DB_LIMIT = 2700.0  # if best candidate mirror has failed within last 2700 seconds, it warrants a db refresh
MINIMUM_WAIT_BETWEEN_MIRROR_DB_REFRESH = 1800.0  # db is not refreshed more frequently than this number of seconds
WAIT_INTERVAL_WHEN_NO_MIRRORS_AVAILABLE = 60.0
MIRROR_TEST_TIMEOUT_LIMIT = 16.0
NR_OF_TRIES_PER_MIRROR = 10

DARKFAIL_URL = "dark.fail"
DARKFAIL_MARKET_STRINGS = {
    EMPIRE_MARKET_ID: "Empire Market",
    CRYPTONIA_MARKET_ID: "Cryptonia Market",
    SAMSARA_MARKET_ID: "Samsara Market",
}
DARKFAIL_MARKET_SUBURLS = {
    EMPIRE_MARKET_ID: "empire",
    CRYPTONIA_MARKET_ID: "cryptonia",
    SAMSARA_MARKET_ID: "samsara",
}

Base = declarative_base()
MARKET_IDS: Tuple[str, ...] = (EMPIRE_MARKET_ID, CRYPTONIA_MARKET_ID)

for market_id in MARKET_IDS:
    assert market_id in DARKFAIL_MARKET_STRINGS.keys()
    assert market_id in DARKFAIL_MARKET_SUBURLS.keys()
WEB_EXCEPTIONS_TUPLE = (requests.HTTPError, urllib3.exceptions.HTTPError, requests.RequestException)
DB_EXCEPTIONS_TUPLE = (SQLAlchemyError, MySQLError, AttributeError, SystemError, DatabaseError, DeadMirrorException)