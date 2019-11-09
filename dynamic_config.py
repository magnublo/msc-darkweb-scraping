from _mysql_connector import MySQLError
from typing import List, Tuple, Type

import requests
import urllib3
from sqlalchemy.exc import SQLAlchemyError, DatabaseError

from definitions import EMPIRE_MARKET_ID, CRYPTONIA_MARKET_ID, MARKET_IDS, EMPIRE_MIN_CREDENTIALS_PER_THREAD, \
    CRYPTONIA_MIN_CREDENTIALS_PER_THREAD
from src.base.base_logger import BaseClassWithLogger
from src.base.base_scraper import BaseScraper
from src.base.base_scraping_manager import ScrapingManager
from src.cryptonia.cryptonia_scrape import CryptoniaScrapingSession
from src.empire.empire_scrape import EmpireScrapingSession
from src.utils import get_logger_name, DeadMirrorException

grey = "\x1b[38;21m"
yellow = "\x1b[33;21m"
red = "\x1b[31;21m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"

LOGGER_VARIABLE_NAME_SUFFIX = "logger"

CLASSES: List[BaseClassWithLogger] = [BaseScraper, ScrapingManager, CryptoniaScrapingSession, EmpireScrapingSession] #TODO: DRY. Iterate over this list

_BASE_CLASS_FORMATTER_CONFIGS = { #TODO: Give each logger a handler for each severity level with a colored format for each severity level
    get_logger_name(BaseScraper.__name__): {
        'format': f'%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        'datefmt': '%d.%m.%y %H:%M:%S'
    },
    get_logger_name(ScrapingManager.__name__): {
        'format': f'[%(levelname)s] %(name)s: %(message)s',
    }
}

CLASS_FORMATTER_CONFIGS = {
    get_logger_name(CryptoniaScrapingSession.__name__): _BASE_CLASS_FORMATTER_CONFIGS[get_logger_name(BaseScraper.__name__)],
    get_logger_name(EmpireScrapingSession.__name__): _BASE_CLASS_FORMATTER_CONFIGS[get_logger_name(BaseScraper.__name__)],
}

CLASS_FORMATTER_CONFIGS.update(_BASE_CLASS_FORMATTER_CONFIGS)

_BASE_CLASS_HANDLER_CONFIGS = {
    get_logger_name(BaseScraper.__name__): {
        'level': 'INFO',
        'formatter': get_logger_name(BaseScraper.__name__),
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',  # Default is stderr
    },
    get_logger_name(ScrapingManager.__name__): {
        'level': 'INFO',
        'formatter': get_logger_name(ScrapingManager.__name__),
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',  # Default is stderr
    }
}

CLASS_HANDLER_CONFIGS = {
    get_logger_name(CryptoniaScrapingSession.__name__): _BASE_CLASS_HANDLER_CONFIGS[get_logger_name(BaseScraper.__name__)],
    get_logger_name(EmpireScrapingSession.__name__): _BASE_CLASS_HANDLER_CONFIGS[get_logger_name(BaseScraper.__name__)],
}

CLASS_HANDLER_CONFIGS.update(_BASE_CLASS_HANDLER_CONFIGS)

_BASE_CLASS_LOGGER_CONFIGS = {
    get_logger_name(BaseScraper.__name__): {
        'handlers': [get_logger_name(BaseScraper.__name__)],
        'level': 'INFO',
        'propagate': False
    },
    get_logger_name(ScrapingManager.__name__): {
        'handlers': [get_logger_name(ScrapingManager.__name__)],
        'level': 'INFO',
        'propagate': False
    }
}

CLASS_LOGGER_CONFIGS = {
    get_logger_name(CryptoniaScrapingSession.__name__): _BASE_CLASS_LOGGER_CONFIGS[get_logger_name(BaseScraper.__name__)],
    get_logger_name(EmpireScrapingSession.__name__): _BASE_CLASS_LOGGER_CONFIGS[get_logger_name(BaseScraper.__name__)],
}

CLASS_LOGGER_CONFIGS.update(_BASE_CLASS_LOGGER_CONFIGS)

BASE_LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%e:%m:%y %H:%M:%S'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
    }
}

SCRAPER_CLASSES: Tuple[object, ...] = (EmpireScrapingSession, CryptoniaScrapingSession)

assert len(MARKET_IDS) == len(SCRAPER_CLASSES)

WEBSITES_TO_BE_SCRAPED: Tuple[Tuple[str, int, Type[BaseScraper]], ...] = (
    (EMPIRE_MARKET_ID, EMPIRE_MIN_CREDENTIALS_PER_THREAD, EmpireScrapingSession),
    (CRYPTONIA_MARKET_ID, CRYPTONIA_MIN_CREDENTIALS_PER_THREAD, CryptoniaScrapingSession)
)

assert len(MARKET_IDS) == len(WEBSITES_TO_BE_SCRAPED)

def get_logger_config() -> dict:
    config = BASE_LOGGER_CONFIG
    config['loggers'].update(CLASS_LOGGER_CONFIGS)
    config['handlers'].update(CLASS_HANDLER_CONFIGS)
    config['formatters'].update(CLASS_FORMATTER_CONFIGS)
    return config


WEB_EXCEPTIONS_TUPLE = (requests.HTTPError, urllib3.exceptions.HTTPError, requests.RequestException)
DB_EXCEPTIONS_TUPLE = (SQLAlchemyError, MySQLError, AttributeError, SystemError, DatabaseError, DeadMirrorException)