import datetime

from sqlalchemy import Column, Integer, DateTime, CHAR, Boolean, String

from definitions import MARKET_NAME_COLUMN_LENGTH, Base

TABLE_NAME = 'scraping_session'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class ScrapingSession(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    market = Column(CHAR(MARKET_NAME_COLUMN_LENGTH))
    duplicates_encountered = Column(Integer)
    nr_of_threads = Column(Integer)
    initial_queue_size = Column(Integer)
    time_started = Column(DateTime, default=datetime.datetime.utcnow)
    time_finished = Column(DateTime)
    exited_gracefully = Column(Boolean, default=False, index=True)
    host_system_fqdn = Column(String(32))