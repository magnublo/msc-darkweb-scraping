from sqlalchemy import Column, Integer, Boolean, CHAR

from definitions import MARKET_NAME_COLUMN_LENGTH, Base

TABLE_NAME = 'settings'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Settings(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    market = Column(CHAR(MARKET_NAME_COLUMN_LENGTH), nullable=False)
    refill_queue_when_complete = Column(Boolean, nullable=False)

