from src.cryptonia.cryptonia_scrape import CryptoniaMarketScraper

LOGGER_VARIABLE_NAME_SUFFIX = "logger"


CLASS_HANDLER_CONFIGS = {
    CryptoniaMarketScraper.__name__: {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
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
    config['loggers'].update(CLASS_HANDLER_CONFIGS)
    return config


