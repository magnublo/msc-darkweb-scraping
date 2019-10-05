from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from definitions import DEBUG_MODE, DB_ENGINE_URL, DB_CLIENT_ENCODING
from src.empire.scrapeManager import EmpireScrapingManager

engine = create_engine(DB_ENGINE_URL, encoding=DB_CLIENT_ENCODING)
Session = sessionmaker(bind=engine)
Base = declarative_base()

if DEBUG_MODE:
    nr_of_threads = 1
else:
    nr_of_threads = input("Nr. of threads: ")

scraping_manager = EmpireScrapingManager(nr_of_threads=int(nr_of_threads))