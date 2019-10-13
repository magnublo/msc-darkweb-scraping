import datetime

from sqlalchemy import Column, DateTime, Integer, String, Date, UniqueConstraint

from definitions import Base

TABLE_NAME = 'seller'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Seller(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    name = Column(String)
    registration_date = Column(Date)
    market = Column(String)

    UniqueConstraint(name, market)