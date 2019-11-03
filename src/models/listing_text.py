import datetime

from sqlalchemy import Column, Text, DateTime, CHAR

from definitions import Base

TABLE_NAME = 'listing_text'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class ListingText(Base):

    __tablename__ = TABLE_NAME

    id = Column(CHAR(32), primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text) # max 16384 on cryptonia

