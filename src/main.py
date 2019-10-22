import faulthandler
import threading

import demoji

from definitions import Base, EMPIRE_MARKET_ID, CRYPTONIA_MARKET_ID
from environmentSettings import DEBUG_MODE, DB_USERNAME, log
from src.cryptonia.cryptonia_scrape_manager import CryptoniaScrapingManager
from src.db_utils import kill_all_existing_db_connections_for_user, get_engine, get_db_session, set_settings, \
    fix_integrity_of_database, get_settings
from src.empire.empire_scrape_manager import EmpireScrapingManager

faulthandler.enable()

log.info("info message")

if DEBUG_MODE:
    cryptonia_nr_of_threads = 0
    cryptonia_start_immediately = True

    empire_nr_of_threads = 1
    empire_start_immediately = True
else:
    empire_nr_of_threads = int(input(f"[{EMPIRE_MARKET_ID}] Nr. of threads: "))
    empire_start_immediately = bool(input(f"[{EMPIRE_MARKET_ID}] Start immediately? (True/False)"))

    cryptonia_nr_of_threads = int(input(f"[{CRYPTONIA_MARKET_ID}] Nr. of threads: "))
    cryptonia_start_immediately = bool(input(f"[{CRYPTONIA_MARKET_ID}] Start immediately? (True/False)"))

if not demoji.last_downloaded_timestamp():
    demoji.download_codes()

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
cryptonia_scraping_manager = EmpireScrapingManager(settings=empire_settings, nr_of_threads=int(empire_nr_of_threads))
cryptonia_thread = threading.Thread(target=cryptonia_scraping_manager.run, args=(empire_start_immediately,))
cryptonia_thread.start()

# cryptonia market
cryptonia_scraping_manager = CryptoniaScrapingManager(settings=cryptonia_settings, nr_of_threads=int(cryptonia_nr_of_threads))
cryptonia_thread = threading.Thread(target=cryptonia_scraping_manager.run, args=(cryptonia_start_immediately,))
cryptonia_thread.start()