import datetime

from sqlalchemy import Column, String, Integer, Date, ForeignKey, Boolean, DateTime, Float

import src.models.country as country
import src.models.listing_text as listing_text
import src.models.scraping_session as scraping_session
from src.base import Base

TABLE_NAME = 'listing_observation'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY

class ListingObservation(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY))
    listing_text_id = Column(String, ForeignKey(listing_text.TABLE_NAME_AND_PRIMARY_KEY))

    title = Column(String)
    category = Column(String)

    btc = Column(Boolean)
    ltc = Column(Boolean)
    xmr = Column(Boolean)
    seller = Column(String)
    price = Column(Float)
    fiat_currency = Column(String)
    origin_country = Column(String, ForeignKey(country.TABLE_NAME_AND_PRIMARY_KEY))
    # destination_country is represented in junction table

    # Vendor specific attributes. These attributes may have null values.
    btc_rate = Column(Float)
    ltc_rate = Column(Float)
    xmr_rate = Column(Float)
    nr_sold = Column(Integer)
    nr_sold_since_date = Column(Date)
    vendor_level = Column(Integer)
    trust_level = Column(Integer)


