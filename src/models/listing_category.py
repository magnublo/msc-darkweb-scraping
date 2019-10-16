import datetime

from sqlalchemy import Column, String, DateTime, Integer, UniqueConstraint, CHAR

from definitions import MARKET_NAME_COLUMN_LENGTH, Base

TABLE_NAME = 'listing_category'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

WEBSITE_CATEGORY_ID_COLUMN_NAME = "website_id"
MARKET_NAME_COLUMN_NAME = "name"
MARKET_ID_COLUMN_NAME = "market"

class ListingCategory(Base):

    __tablename__ = TABLE_NAME
    __table_args__ = (UniqueConstraint(WEBSITE_CATEGORY_ID_COLUMN_NAME, MARKET_NAME_COLUMN_NAME, MARKET_ID_COLUMN_NAME),)

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    website_id = Column(WEBSITE_CATEGORY_ID_COLUMN_NAME, Integer) #the id on this category as denoted by the host website
    name = Column(MARKET_NAME_COLUMN_NAME, String) #the printed name of the category on the host website
    market = Column(MARKET_ID_COLUMN_NAME, CHAR(MARKET_NAME_COLUMN_LENGTH)) #the unique id of the host website/market, as specified in this script
