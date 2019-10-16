import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float, UniqueConstraint, CHAR

from definitions import Base, MYSQL_CASCADE, CREATED_DATE_COLUMN_NAME, URL_COLUMN_LENGTH
from src.models import scraping_session
from src.models import seller
from src.models import seller_description_text

TABLE_NAME = 'seller_observation'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class SellerObservation(Base):

    __tablename__ = TABLE_NAME
    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(CREATED_DATE_COLUMN_NAME, DateTime, default=datetime.datetime.utcnow)
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    url = Column(String(URL_COLUMN_LENGTH))

    seller_id = Column(Integer, ForeignKey(seller.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    description = Column(CHAR(32), ForeignKey(seller_description_text.TABLE_NAME_AND_PRIMARY_KEY))
    disputes = Column(Integer)
    orders = Column(Integer)
    spendings = Column(String)
    feedback_left = Column(Integer)
    feedback_percent_positive = Column(Float)
    last_online = Column(Date)

    dream_market_successful_sales = Column(Integer)
    dream_market_star_rating = Column(Float)
    wall_street_market_successful_sales = Column(Integer)
    wall_street_market_star_rating = Column(Float)

    parenthesis_number = Column(Integer)
    positive_feedback_received_percent = Column(Float)

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

    UniqueConstraint(session_id, url)