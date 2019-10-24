from typing import List

from src.base_logger import BaseClassWithLogger
from src.base_scraper import BaseScraper
from src.base_scraping_manager import BaseScrapingManager
from src.cryptonia.cryptonia_scrape import CryptoniaScrapingSession
from src.cryptonia.cryptonia_scrape_manager import CryptoniaScrapingManager
from src.empire.empire_scrape import EmpireScrapingSession
from src.empire.empire_scrape_manager import EmpireScrapingManager

LOGGER_VARIABLE_NAME_SUFFIX = "logger"

CLASSES: List[BaseClassWithLogger] = [BaseScraper, BaseScrapingManager, CryptoniaScrapingSession,
                                      CryptoniaScrapingManager, EmpireScrapingSession,
                                      EmpireScrapingManager]

_BASE_CLASS_FORMATTER_CONFIGS = {
    BaseScraper.__name__: {
        {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%e:%m:%y %H:%M:%S'
        }
    },
    BaseScrapingManager.__name__: {
        'format': '[%(levelname)s] %(name)s: %(message)s',
    }
}

CLASS_FORMATTER_CONFIGS = {
    CryptoniaScrapingSession.__name__: {
        _BASE_CLASS_FORMATTER_CONFIGS[BaseScraper.__name__]
    },
    CryptoniaScrapingManager.__name__: {
        _BASE_CLASS_FORMATTER_CONFIGS[BaseScrapingManager.__name__]
    },
    EmpireScrapingSession.__name__: {
        _BASE_CLASS_FORMATTER_CONFIGS[BaseScraper.__name__]
    },
    EmpireScrapingManager.__name__: {
        _BASE_CLASS_FORMATTER_CONFIGS[BaseScrapingManager.__name__]
    },
}

_BASE_CLASS_HANDLER_CONFIGS = {
    BaseScraper.__name__: {
        'level': 'INFO',
        # 'formatter': BaseScraper.__name__,
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',  # Default is stderr
    },
    BaseScrapingManager.__name__: {
        'level': 'INFO',
        # 'formatter': BaseScrapingManager.__name__,
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',  # Default is stderr
    }
}

CLASS_HANDLER_CONFIGS = {
    CryptoniaScrapingSession.__name__: {
        _BASE_CLASS_HANDLER_CONFIGS[BaseScraper.__name__]
    },
    CryptoniaScrapingManager.__name__: {
        _BASE_CLASS_HANDLER_CONFIGS[BaseScrapingManager.__name__]
    },

    EmpireScrapingSession.__name__: {
        _BASE_CLASS_HANDLER_CONFIGS[BaseScraper.__name__]
    },
    EmpireScrapingManager.__name__: {
        _BASE_CLASS_HANDLER_CONFIGS[BaseScrapingManager.__name__]
    },
}

CLASS_HANDLER_CONFIGS.update(_BASE_CLASS_HANDLER_CONFIGS)

_BASE_CLASS_LOGGER_CONFIGS = {
    BaseScraper.__name__: {
        # 'handlers': [BaseScraper.__name__],
        'level': 'INFO',
        'propagate': False
    },
    BaseScrapingManager.__name__: {
        # 'handlers': [BaseScrapingManager.__name__],
        'level': 'INFO',
        'propagate': False
    }
}

CLASS_LOGGER_CONFIGS = {
    CryptoniaScrapingSession.__name__: {
        _BASE_CLASS_LOGGER_CONFIGS[BaseScraper.__name__]
    },
    EmpireScrapingSession.__name__: {
        _BASE_CLASS_LOGGER_CONFIGS[BaseScraper.__name__]
    },
    CryptoniaScrapingManager.__name__: {
        _BASE_CLASS_LOGGER_CONFIGS[BaseScrapingManager.__name__]
    },
    EmpireScrapingManager.__name__: {
        _BASE_CLASS_LOGGER_CONFIGS[BaseScrapingManager.__name__]
    }
}

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


def get_logger_config() -> dict:
    config = BASE_LOGGER_CONFIG
    config['loggers'].update(CLASS_LOGGER_CONFIGS)
    config['handlers'].update(CLASS_HANDLER_CONFIGS)
    for a_class in CLASSES:
        config['handlers'][a_class.__name__]['formatter'] = CLASS_FORMATTER_CONFIGS[a_class.__name__]
        config['loggers'][a_class.__name__]['handlers'] = CLASS_HANDLER_CONFIGS[a_class.__name__]
    return config
