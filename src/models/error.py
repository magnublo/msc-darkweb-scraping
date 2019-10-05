import datetime

from sqlalchemy import Column, String, Text, DateTime, Integer

from src.base import Base

TABLE_NAME = 'error'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Error(Base):

    __tablename__ = TABLE_NAME

    id = Column(String, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    session_id = Column(Integer)
    thread_id = Column(Integer)
    text = Column(Text)

