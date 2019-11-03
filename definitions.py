import os
from typing import Tuple, List

from sqlalchemy.ext.declarative import declarative_base

from environment_settings import MYSQL_ECHO_DEBUG

ONE_WEEK = 3600*24*7
ONE_DAY = 3600*24
ONE_HOUR = 3600

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
ROOT_SRC_DIR = ROOT_DIR + "src/"
WORKING_DIR = os.getcwd() + "/"

RECOMMENDED_NR_OF_THREADS_PER_TOR_PROXY = 4
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
DEAD_MIRROR_TIMEOUT = 1200
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
PRODUCT_TITLE_COLUMN_LENGTH = 64 #Confirmed max on cryptonia
PRODUCT_CATEGORY_NAME_COLUMN_LENGTH = 40
CREATED_DATE_COLUMN_NAME = "created_date"


BEAUTIFUL_SOUP_HTML_PARSER = "lxml"

ANTI_CAPTCHA_ACCOUNT_KEY = "6c5815eb3db205d9c4a05ba6941b0a3a"
ANTI_CAPTCHA_CREATE_TASK_URL = "http://api.anti-captcha.com/createTask"
ANTI_CAPTCHA_GET_TASK_URL = "https://api.anti-captcha.com/getTaskResult"
ANTI_CAPTCHA_WAIT_INTERVAL = 2
ANTI_CAPTCHA_INITIAL_WAIT_INTERVAL = 6

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
EMPIRE_MARKET_LOGIN_URL = "http://" + EMPIRE_MARKET_URL + "/index/login"
EMPIRE_MARKET_HOME_URL = "http://" + EMPIRE_MARKET_URL + "/home"
EMPIRE_BASE_CATEGORY_URL = "http://" + EMPIRE_MARKET_URL + "/category/"
EMPIRE_MARKET_ID = "EMPIRE_MARKET"
EMPIRE_SRC_DIR = ROOT_SRC_DIR + "empire/"
EMPIRE_HTTP_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

EMPIRE_MARKET_LOGIN_PHRASE = "Welcome to Empire Market! Please login to access the marketplace."
EMPIRE_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE = "There is currently nothing to show."

EMPIRE_MARKET_EXTERNAL_MARKET_STRINGS: List[Tuple[str, str]] = [
    (DREAM_MARKET_ID, "Dream Market"),
    (WALL_STREET_MARKET_ID, "Wall Street Market")
]


#CRYPTONIA MARKET
CRYPTONIA_MARKET_ID = "CRYPTONIA_MARKET"
CRYPTONIA_MARKET_BASE_URL = "http://bntee6mf5w2okbpxdxheq7bk36yfmwithltxubliyvum6wlrrxzn72id.onion"
CRYPTONIA_MARKET_CATEGORY_INDEX_URL_PATH = "/products"
CRYPTONIA_MARKET_CREDENTIALS = [["usingPython3", "Password123!"]]
CRYPTONIA_DIR = ROOT_DIR + "src/cryptonia/"
CRYPTONIA_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE = "No products found."
CRYPTONIA_PHYSICAL_LISTING_TYPE_STRING = "Physical Listing"
CRYPTONIA_WORLD_COUNTRY = "Worldwide"
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
    (BLACK_BANK_MARKET_ID, "Black Bank"),
    (AGORA_MARKET_ID, "Agora:"),
    (BLACK_MARKET_RELOADED_ID, "Black Market Reloaded:"),
    (ABRAXAS_MARKET_ID, "Abraxas:"),
    (MIDDLE_EARTH_MARKET_ID, "Middle Earth:")
]


Base = declarative_base()
MARKET_IDS: Tuple[str, ...] = (EMPIRE_MARKET_ID, CRYPTONIA_MARKET_ID)