import datetime

from sqlalchemy import Column, DateTime, Integer, Date, UniqueConstraint, CHAR

from definitions import SELLER_NAME_COLUMN_LENGTH, MARKET_NAME_COLUMN_LENGTH, Base

TABLE_NAME = 'seller'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Seller(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    name = Column(CHAR(SELLER_NAME_COLUMN_LENGTH))
    registration_date = Column(DateTime)
    market = Column(CHAR(MARKET_NAME_COLUMN_LENGTH))

    UniqueConstraint(name, market)