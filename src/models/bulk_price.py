import datetime

from sqlalchemy import Column, DateTime, Integer, Float

from definitions import Base

TABLE_NAME = 'bulk_price'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class BulkPrice(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    unit_limit = Column(Float)
    unit_fiat_price = Column(Float)
    unit_btc_price = Column(Float)
    discount_percent = Column(Float)


