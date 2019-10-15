import faulthandler

from definitions import Base
from environmentSettings import DEBUG_MODE, DB_USERNAME
from src.empire.scrapeManager import EmpireScrapingManager
from src.utils import get_engine, kill_all_existing_db_connections_for_user

faulthandler.enable()

if DEBUG_MODE:
    nr_of_threads = 5
else:
    nr_of_threads = input("Nr. of threads: ")

kill_all_existing_db_connections_for_user(DB_USERNAME)
engine = get_engine()
Base.metadata.create_all(engine)
scraping_manager = EmpireScrapingManager(nr_of_threads=int(nr_of_threads))