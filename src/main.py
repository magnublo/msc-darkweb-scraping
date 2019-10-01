from src.empire.scrapeManager import EmpireScrapingManager

nr_of_threads = input("Nr. of threads: ")
scraping_manager = EmpireScrapingManager(nr_of_threads=int(nr_of_threads))