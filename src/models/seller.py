import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey

from src.base import Base
from src.models import scraping_session

TABLE_NAME = 'seller'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class SellerObservation(Base):

    __tablename__ = TABLE_NAME
    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY))
    name = Column(String)
    nr_sold = Column(Integer)
    nr_sold_since_date = Column(Date)
    market = Column(String)