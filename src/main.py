from definitions import DEBUG_MODE, Base, engine
from src.empire.scrapeManager import EmpireScrapingManager

if DEBUG_MODE:
    nr_of_threads = 1
else:
    nr_of_threads = input("Nr. of threads: ")

Base.metadata.create_all(engine)
scraping_manager = EmpireScrapingManager(nr_of_threads=int(nr_of_threads))