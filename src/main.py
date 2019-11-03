import faulthandler
import threading
from logging.config import dictConfig
from typing import Type

import demoji

from definitions import Base, MARKET_IDS
from dynamic_config import get_logger_config, SCRAPER_CLASSES, WEBSITES_TO_BE_SCRAPED
from environment_settings import DB_USERNAME
from src.base_scraping_manager import ScrapingManager
from src.db_utils import kill_all_existing_db_connections_for_user, set_settings, \
    get_engine, get_db_session, get_settings
from src.tor_proxy_check import get_available_tor_proxies
from src.utils import get_proxies, get_user_input


def run():
    faulthandler.enable()
    dictConfig(get_logger_config())

    user_input = get_user_input()

    if not demoji.last_downloaded_timestamp():
        demoji.download_codes()

    # TODO: Implement logic to loop over the markets. DRY
    # TODO: Impement logic to check that Tor server has one port per thread

    thread_counts = tuple(usr_input[0] for usr_input in user_input)
    total_nr_of_threads = sum(thread_counts)

    available_ports = get_available_tor_proxies(total_nr_of_threads=total_nr_of_threads)
    available_proxies = get_proxies(web_site_thread_counts=thread_counts,
                                    available_proxy_ports=available_ports)

    kill_all_existing_db_connections_for_user(DB_USERNAME)
    engine = get_engine()
    db_session = get_db_session(engine)
    # fix_integrity_of_database(db_session)
    Base.metadata.create_all(engine)

    for (market_id, market_credentials, scraper_class), (
    nr_of_threads, session_id, should_start_immediately), proxies in zip(
            WEBSITES_TO_BE_SCRAPED, user_input, available_proxies):
        set_settings(db_session, market_name=market_id)
        settings = get_settings(db_session=db_session, market_name=market_id)
        scraping_manager = ScrapingManager(settings=settings, nr_of_threads=nr_of_threads,
                                           initial_session_id=session_id, proxies=proxies,
                                           scraper_class=scraper_class, market_credentials=market_credentials,
                                           market_id=market_id)
        thread = threading.Thread(target=scraping_manager.run, args=(should_start_immediately,))
        thread.start()

    db_session.expunge_all()
    db_session.close()
