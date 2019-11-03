import datetime

from sqlalchemy import Column, DateTime, Integer, ForeignKey, String, Text

from definitions import Base, MYSQL_VARCHAR_DEFAULT_LENGTH, MYSQL_SET_NULL
from src.models import scraping_session

TABLE_NAME = 'web_session_cookie'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY


class WebSessionCookie(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    updated_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    thread_id = Column(Integer)
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_SET_NULL))

    username = Column(String(16))
    mirror_url = Column(String(MYSQL_VARCHAR_DEFAULT_LENGTH))
    name = Column(String(MYSQL_VARCHAR_DEFAULT_LENGTH))
    value = Column(String(MYSQL_VARCHAR_DEFAULT_LENGTH))
    python_object = Column(Text)
