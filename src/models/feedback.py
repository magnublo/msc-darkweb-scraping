import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, Text, CHAR

import src.models.seller as seller
from definitions import MYSQL_CASCADE, CREATED_DATE_COLUMN_NAME, FEEDBACK_TEXT_HASH_COLUMN_LENGTH, \
    URL_COLUMN_LENGTH, FEEDBACK_BUYER_COLUMN_LENGTH, FEEDBACK_CATEGORY_COLUMN_LENGTH, CURRENCY_COLUMN_LENGTH, \
    MARKET_NAME_COLUMN_LENGTH, Base
from src.models import scraping_session

TABLE_NAME = 'feedback'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY

class Feedback(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    created_date = Column(CREATED_DATE_COLUMN_NAME, DateTime, default=datetime.datetime.utcnow)
    date_published = Column(DateTime)
    market = Column(CHAR(MARKET_NAME_COLUMN_LENGTH))
    seller_id = Column(Integer, ForeignKey(seller.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    product_url = Column(String(URL_COLUMN_LENGTH))
    session_id = Column(Integer, ForeignKey(scraping_session.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))

    feedback_message_text = Column(Text)
    seller_response_message = Column(Text)
    text_hash = Column(CHAR(FEEDBACK_TEXT_HASH_COLUMN_LENGTH))
    category = Column(CHAR(FEEDBACK_CATEGORY_COLUMN_LENGTH))

    buyer = Column(CHAR(FEEDBACK_BUYER_COLUMN_LENGTH))
    currency = Column(CHAR(CURRENCY_COLUMN_LENGTH))
    price = Column(Float)


