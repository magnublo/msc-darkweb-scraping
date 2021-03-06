import datetime

from sqlalchemy import Column, DateTime, Integer, Float, CHAR, ForeignKey, Boolean, String

from definitions import CURRENCY_COLUMN_LENGTH, MYSQL_CASCADE, Base
from src.models import listing_observation

TABLE_NAME = 'shipping_method'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY


class ShippingMethod(Base):
    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    listing_observation_id = Column(Integer,
                                    ForeignKey(listing_observation.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))

    description = Column(String(128))
    price = Column(Float)
    fiat_currency = Column(CHAR(CURRENCY_COLUMN_LENGTH))

    #empire
    days_shipping_time = Column(Float)  # fractional number of days do appear in listings
    quantity_unit_name = Column(CHAR(6))
    price_is_per_unit = Column(Boolean)