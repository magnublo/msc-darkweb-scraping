from sqlalchemy import Column, String, Float, Integer

from src.base import Base

TABLE_NAME = 'scraping_session'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class ScrapingSession(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    market = Column(String)
    time_started = Column(Float)
    time_finished = Column(Float)
