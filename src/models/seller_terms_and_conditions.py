import datetime

from sqlalchemy import Column, Text, DateTime, CHAR, Integer, UniqueConstraint

from definitions import Base

TABLE_NAME = 'seller_terms_and_conditions'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class SellerTermsAndConditions(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text, nullable=False)
    text_hash = Column(CHAR(32), nullable=False)
    UniqueConstraint(text_hash)

