import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, Text

import src.models.seller_observation as seller
from definitions import Base
from src.models import scraping_session

TABLE_NAME = 'feedback'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY

class Feedback(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    date_published = Column(DateTime)
    market = Column(String)
    seller_id = Column(Integer, ForeignKey(seller.TABLE_NAME_AND_PRIMARY_KEY))
    listing_title = Column(String)
    product_url = Column(String)
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY))

    feedback_message_text = Column(Text)
    seller_response_message = Column(Text)
    text_hash = Column(String)
    category = Column(String)

    buyer = Column(String)
    currency = Column(String)
    price = Column(Float)


