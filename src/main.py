import faulthandler
import threading
from logging.config import dictConfig

import demoji

from definitions import Base, EMPIRE_MARKET_ID, CRYPTONIA_MARKET_ID
from environment_settings import DEBUG_MODE, DB_USERNAME
from logger_config import get_logger_config
from src.cryptonia.cryptonia_scrape_manager import CryptoniaScrapingManager
from src.db_utils import kill_all_existing_db_connections_for_user, set_settings, \
    fix_integrity_of_database, get_engine, get_db_session, get_settings
from src.empire.empire_scrape_manager import EmpireScrapingManager
from src.tor_proxy_check import get_available_tor_proxies
from src.utils import get_proxies

faulthandler.enable()
dictConfig(get_logger_config())

if DEBUG_MODE:
    empire_nr_of_threads = 0
    empire_session_id = None
    empire_start_immediately = True

    cryptonia_nr_of_threads = 1
    cryptonia_session_id = None
    cryptonia_start_immediately = True

else:
    empire_nr_of_threads = int(input(f"[{EMPIRE_MARKET_ID}] Nr. of threads: "))
    try:
        empire_session_id = int(input(f"[{EMPIRE_MARKET_ID}] Resume session_id [blank makes new]: "))
    except ValueError:
        empire_session_id = None
    empire_start_immediately = bool(input(f"[{EMPIRE_MARKET_ID}] Start immediately? (True/False)"))

    cryptonia_nr_of_threads = int(input(f"[{CRYPTONIA_MARKET_ID}] Nr. of threads: "))
    try:
        cryptonia_session_id = int(input(f"[{CRYPTONIA_MARKET_ID}] Resume session_id [blank makes new]: "))
    except ValueError:
        cryptonia_session_id = None
    cryptonia_start_immediately = bool(input(f"[{CRYPTONIA_MARKET_ID}] Start immediately? (True/False)"))

if not demoji.last_downloaded_timestamp():
    demoji.download_codes()

#TODO: Implement logic to loop over the markets. DRY
#TODO: Impement logic to check that Tor server has one port per thread

total_nr_of_threads = empire_nr_of_threads+cryptonia_nr_of_threads

available_ports = get_available_tor_proxies(total_nr_of_threads=total_nr_of_threads)
available_proxies = get_proxies((empire_nr_of_threads, cryptonia_nr_of_threads), available_proxy_ports=available_ports)

kill_all_existing_db_connections_for_user(DB_USERNAME)
engine = get_engine()
db_session = get_db_session(engine)
fix_integrity_of_database(db_session)

# empire market
set_settings(db_session, market_name=EMPIRE_MARKET_ID)
empire_settings = get_settings(db_session=db_session, market_name=EMPIRE_MARKET_ID)

# cryptonia market
set_settings(db_session, market_name=CRYPTONIA_MARKET_ID)
cryptonia_settings = get_settings(db_session=db_session, market_name=CRYPTONIA_MARKET_ID)

db_session.expunge_all()
db_session.close()

Base.metadata.create_all(engine)

# empire market
empire_scraping_manager = EmpireScrapingManager(settings=empire_settings, nr_of_threads=int(empire_nr_of_threads),
                                                initial_session_id=empire_session_id, proxies=available_proxies[0])
empire_thread = threading.Thread(target=empire_scraping_manager.run, args=(empire_start_immediately,))
empire_thread.start()

# cryptonia market
cryptonia_scraping_manager = CryptoniaScrapingManager(settings=cryptonia_settings,
                                                      nr_of_threads=int(cryptonia_nr_of_threads),
                                                      initial_session_id=cryptonia_session_id, proxies=available_proxies[1])
cryptonia_thread = threading.Thread(target=cryptonia_scraping_manager.run, args=(cryptonia_start_immediately,))
cryptonia_thread.start()
