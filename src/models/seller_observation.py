import datetime

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, Float, UniqueConstraint, CHAR, Boolean, String

from definitions import MYSQL_CASCADE, CREATED_DATE_COLUMN_NAME, URL_COLUMN_LENGTH, Base, CURRENCY_COLUMN_LENGTH, \
    XMPP_JABBER_ID_COLUMN_LENGTH
from src.models import description_text
from src.models import scraping_session
from src.models import seller

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
    description = Column(Integer, ForeignKey(description_text.TABLE_NAME_AND_PRIMARY_KEY))
    terms_and_conditions_id = Column(Integer, ForeignKey(description_text.TABLE_NAME_AND_PRIMARY_KEY))
    disputes = Column(Integer)
    last_online = Column(Date) #Within the last 3 days # Within the last 24 hours

    parenthesis_number = Column(Integer)
    positive_feedback_received_percent = Column(Float)
    vendor_level = Column(Integer)

    # empire market columns
    orders = Column(Integer)
    spendings = Column(String(10))
    feedback_left = Column(Integer)
    feedback_percent_positive = Column(Float)

    stealth_rating = Column(Integer)
    quality_rating = Column(Integer)
    value_price_rating = Column(Integer)
    trust_level = Column(Integer)

    positive_1m = Column(Integer)
    positive_6m = Column(Integer)
    positive_12m = Column(Integer)
    neutral_1m = Column(Integer)
    neutral_6m = Column(Integer)
    neutral_12m = Column(Integer)
    negative_1m = Column(Integer)
    negative_6m = Column(Integer)
    negative_12m = Column(Integer)

    banned = Column(Boolean)

    # cryptonia columns
    disputes_won = Column(Integer)
    disputes_lost = Column(Integer)
    cryptocurrency_amount_on_escrow = Column(Float)
    fiat_amount_on_escrow = Column(Float)
    cryptocurrency_unit_on_escrow = Column(CHAR(CURRENCY_COLUMN_LENGTH))
    fiat_unit_on_escrow = Column(CHAR(CURRENCY_COLUMN_LENGTH))
    fe_enabled = Column(Boolean)
    xmpp_jabber_id = Column(String(XMPP_JABBER_ID_COLUMN_LENGTH))

    # apollon
    email = Column(String(255))  # confirmed maximum length
    autofinalized_orders = Column(Integer)

