import datetime

from sqlalchemy import Column, Integer, String, CHAR, DateTime, Boolean, Text

from definitions import Base, MYSQL_VARCHAR_DEFAULT_LENGTH, MARKET_NAME_COLUMN_LENGTH, CREATED_DATE_COLUMN_NAME

TABLE_NAME = 'captcha_solution'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY


class CaptchaSolution(Base):

    __tablename__ = TABLE_NAME
    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(CREATED_DATE_COLUMN_NAME, DateTime, default=datetime.datetime.utcnow)

    image = Column(Text)
    solution = Column(String(MYSQL_VARCHAR_DEFAULT_LENGTH))
    website = Column(CHAR(MARKET_NAME_COLUMN_LENGTH))
    numbers = Column(Boolean)
    letters = Column(Boolean)
    solved_correctly = Column(Boolean)
