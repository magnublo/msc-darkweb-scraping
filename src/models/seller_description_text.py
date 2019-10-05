import datetime

from sqlalchemy import Column, String, Text, DateTime

from src.base import Base

TABLE_NAME = 'seller_description_text'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class SellerDescriptionText(Base):

    __tablename__ = TABLE_NAME

    id = Column(String, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text)

