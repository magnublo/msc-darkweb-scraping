import datetime

from sqlalchemy import Column, Text, DateTime, Integer, String

from definitions import Base

TABLE_NAME = 'error'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Error(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    updated_date = Column(DateTime, onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)
    session_id = Column(Integer)
    thread_id = Column(Integer)
    type = Column(String)
    text = Column(Text)

