import datetime

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, CHAR
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from definitions import ERROR_FINGER_PRINT_COLUMN_LENGTH, MYSQL_CASCADE, Base
from src.models import scraping_session

TABLE_NAME = 'error'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Error(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    updated_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    thread_id = Column(Integer)
    type = Column(String)
    text = Column(MEDIUMTEXT)
    finger_print = Column(CHAR(ERROR_FINGER_PRINT_COLUMN_LENGTH))

