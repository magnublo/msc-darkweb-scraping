import datetime

from sqlalchemy import Column, DateTime, Integer, UniqueConstraint, CHAR, String, ForeignKey

from definitions import MARKET_NAME_COLUMN_LENGTH, Base, PRODUCT_CATEGORY_NAME_COLUMN_LENGTH, MYSQL_SET_NULL

TABLE_NAME = 'listing_category'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY

WEBSITE_CATEGORY_ID_COLUMN_NAME = "website_id"
MARKET_NAME_COLUMN_NAME = "name"
MARKET_ID_COLUMN_NAME = "market"


class ListingCategory(Base):
    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    website_id = Column(WEBSITE_CATEGORY_ID_COLUMN_NAME, Integer)  # the id on this category as denoted by the host
    # website
    name = Column(MARKET_NAME_COLUMN_NAME, CHAR(PRODUCT_CATEGORY_NAME_COLUMN_LENGTH))  # the printed name of the
    # category on the host website
    market = Column(MARKET_ID_COLUMN_NAME, CHAR(MARKET_NAME_COLUMN_LENGTH))  # the unique id of the host
    # website/market, as specified in this script
    parent_category_id = Column(Integer, ForeignKey(TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_SET_NULL))
    level = Column(Integer)

    # UniqueConstraint(name, parent_category, market)
    # TODO: This constraint is valid, but not until EmpireScrapingSession actually parses parent_category field
