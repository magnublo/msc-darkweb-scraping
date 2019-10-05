from definitions import DEBUG_MODE
from src.empire.scrapeManager import EmpireScrapingManager

if DEBUG_MODE:
    nr_of_threads = 1
else:
    nr_of_threads = input("Nr. of threads: ")

scraping_manager = EmpireScrapingManager(nr_of_threads=int(nr_of_threads))