import datetime

from sqlalchemy import Column, Text, DateTime, Integer

from definitions import Base

TABLE_NAME = 'error'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Error(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    updated_date = Column(DateTime, onupdate=datetime.datetime.now)
    session_id = Column(Integer)
    thread_id = Column(Integer)
    text = Column(Text)

