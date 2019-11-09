import datetime

from sqlalchemy import Column, Text, DateTime, CHAR, Integer, UniqueConstraint

from definitions import Base

TABLE_NAME = 'description_text'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY


class DescriptionText(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    text_hash = Column(CHAR(32))
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text)

    UniqueConstraint(text_hash)

