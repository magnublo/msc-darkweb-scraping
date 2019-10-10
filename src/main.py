from definitions import DEBUG_MODE, Base, engine, Session
from src.empire.scrapeManager import EmpireScrapingManager
from src.utils import SynchronizeProxy

if DEBUG_MODE:
    nr_of_threads = 4
else:
    nr_of_threads = input("Nr. of threads: ")

Base.metadata.create_all(engine)
db_session = SynchronizeProxy(Session())
db_session.rollback()
scraping_manager = EmpireScrapingManager(db_session, nr_of_threads=int(nr_of_threads))