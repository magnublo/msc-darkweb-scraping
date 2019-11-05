import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String, CHAR, Float, Index

from definitions import Base, MARKET_NAME_COLUMN_LENGTH, URL_COLUMN_LENGTH

TABLE_NAME = 'market_mirror'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class MarketMirror(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    last_offline_timestamp = Column(Float, default=0)
    last_online_timestamp = Column(Float, nullable=False)
    market_id = Column(CHAR(MARKET_NAME_COLUMN_LENGTH), nullable=False)
    url = Column(String(URL_COLUMN_LENGTH), nullable=False)

    Index(uuid.uuid4(), market_id, url)
    Index(uuid.uuid4(), market_id, last_offline_timestamp, last_online_timestamp)
