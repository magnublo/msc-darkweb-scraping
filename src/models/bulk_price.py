import datetime

from sqlalchemy import Column, DateTime, Integer, Float, ForeignKey

import src.models.listing_observation as listing_observation
from definitions import MYSQL_CASCADE, Base

TABLE_NAME = 'bulk_price'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class BulkPrice(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    listing_observation_id = Column(Integer, ForeignKey(listing_observation.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    unit_amount_lower_bound = Column(Float, nullable=False)
    unit_amount_upper_bound = Column(Float)
    unit_fiat_price = Column(Float)
    unit_btc_price = Column(Float)
    discount_percent = Column(Float)


