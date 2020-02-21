import datetime

from sqlalchemy import Column, Integer, Date, ForeignKey, Boolean, DateTime, Float, CHAR, String

import src.models.country as country
import src.models.scraping_session as scraping_session
import src.models.seller as seller
from definitions import MYSQL_CASCADE, CREATED_DATE_COLUMN_NAME, URL_COLUMN_LENGTH, CURRENCY_COLUMN_LENGTH, Base, \
    PRODUCT_TITLE_COLUMN_LENGTH, MYSQL_VARCHAR_DEFAULT_LENGTH
from src.models import description_text

TABLE_NAME = 'listing_observation'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY

class ListingObservation(Base):
    #TODO: consider adding not-nullable constraints
    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    thread_id = Column(Integer)
    created_date = Column(CREATED_DATE_COLUMN_NAME, DateTime, default=datetime.datetime.utcnow)

    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    listing_text_id = Column(Integer, ForeignKey(description_text.TABLE_NAME_AND_PRIMARY_KEY))

    title = Column(CHAR(PRODUCT_TITLE_COLUMN_LENGTH)) # max 64 characters cryptonia
    url = Column(String(URL_COLUMN_LENGTH))

    btc = Column(Boolean)
    xmr = Column(Boolean)
    btc_multisig = Column(Boolean)

    seller_id = Column(Integer, ForeignKey(seller.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    price = Column(Float)
    fiat_currency = Column(CHAR(CURRENCY_COLUMN_LENGTH))
    origin_country = Column(Integer, ForeignKey(country.TABLE_NAME_AND_PRIMARY_KEY))
    # destination_country is represented in junction table

    btc_rate = Column(Float)
    xmr_rate = Column(Float)
    escrow = Column(Boolean)
    listing_type = Column(String(128)) #cryptonia: Physical, Digital, Autoshop (Digital Listing (Manual Fulfillment))
                                        #empire: Physical Package, Digital,
    quantity_in_stock = Column(Integer)
    # bulk discounts in junction table

    # empire
    promoted_listing = Column(Boolean)
    ltc = Column(Boolean)
    ltc_rate = Column(Float)
    nr_sold = Column(Integer)
    nr_sold_since_date = Column(Date)
    ends_in = Column(String(MYSQL_VARCHAR_DEFAULT_LENGTH)) #TODO: Fix this when possible values are enumerated.
    nr_of_views = Column(Integer)

    # cryptonia
    minimum_order_unit_amount = Column(Integer, default=1)
    unit_type = Column(CHAR(8))

    # apollon
    bch = Column(Boolean)
    bch_rate = Column(Float)
    fifty_percent_finalize_early = Column(Boolean)

    # data analysis
    is_weight_unit_type = Column(Boolean)
    grams_per_unit = Column(Float)
