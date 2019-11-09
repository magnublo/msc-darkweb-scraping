import datetime

from sqlalchemy import Column, DateTime, Integer, String, CHAR, UniqueConstraint, Boolean

from definitions import Base, MARKET_NAME_COLUMN_LENGTH

TABLE_NAME = 'user_credentials'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY


class UserCredential(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)

    thread_id = Column(Integer, default=-1)
    market_id = Column(CHAR(MARKET_NAME_COLUMN_LENGTH))
    username = Column(String(32))
    password = Column(String(128))
    is_registered = Column(Boolean)

    UniqueConstraint(market_id, username)
