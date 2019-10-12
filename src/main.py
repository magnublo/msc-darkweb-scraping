import faulthandler

from definitions import DEBUG_MODE, Base
from src.empire.scrapeManager import EmpireScrapingManager
from src.utils import get_engine

faulthandler.enable()

if DEBUG_MODE:
    nr_of_threads = 4
else:
    nr_of_threads = input("Nr. of threads: ")

engine = get_engine()
Base.metadata.create_all(engine)
scraping_manager = EmpireScrapingManager(engine, nr_of_threads=int(nr_of_threads))