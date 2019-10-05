import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float

from definitions import Base
from src.models import scraping_session
from src.models import seller_description_text

TABLE_NAME = 'seller'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class SellerObservation(Base):

    __tablename__ = TABLE_NAME
    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY))
    market = Column(String)
    url = Column(String)

    name = Column(String)
    description = Column(String, ForeignKey(seller_description_text.TABLE_NAME_AND_PRIMARY_KEY))
    disputes = Column(Integer)
    orders = Column(Integer)
    spendings = Column(String)
    feedback_left = Column(Integer)
    feedback_percent_positive = Column(Float)
    last_online = Column(Date)

    parenthesis_number = Column(Integer)
    dream_market_successful_sales = Column(Integer)
    dream_market_star_rating = Column(Float)
    positive_feedback_received_percent = Column(Float)
    registration_date = Column(Date)

    positive_1m = Column(Integer)
    positive_6m = Column(Integer)
    positive_12m = Column(Integer)
    neutral_1m = Column(Integer)
    neutral_6m = Column(Integer)
    neutral_12m = Column(Integer)
    negative_1m = Column(Integer)
    negative_6m = Column(Integer)
    negative_12m = Column(Integer)

    stealth_rating = Column(Integer)
    quality_rating = Column(Integer)
    value_price_rating = Column(Integer)

    vendor_level = Column(Integer)
    trust_level = Column(Integer)
