import faulthandler

import demoji

from definitions import Base
from environmentSettings import DEBUG_MODE, DB_USERNAME
from src.db_utils import kill_all_existing_db_connections_for_user, get_engine, get_db_session, set_settings, \
    fix_integrity_of_database, get_settings
from src.empire.scrapeManager import EmpireScrapingManager

faulthandler.enable()

if DEBUG_MODE:
    nr_of_threads = 5
else:
    nr_of_threads = input("Nr. of threads: ")

if not demoji.last_downloaded_timestamp():
    demoji.download_codes()

kill_all_existing_db_connections_for_user(DB_USERNAME)
engine = get_engine()
db_session = get_db_session(engine)
fix_integrity_of_database(db_session)
set_settings(db_session)
settings = get_settings(db_session)
db_session.expunge_all()
db_session.close()

Base.metadata.create_all(engine)
scraping_manager = EmpireScrapingManager(settings=settings, nr_of_threads=int(nr_of_threads))