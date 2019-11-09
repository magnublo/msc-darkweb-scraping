import datetime

from sqlalchemy import Column, Text, Integer, ForeignKey, DateTime, CHAR, UniqueConstraint

from definitions import MYSQL_CASCADE, Base
from src.models import seller

TABLE_NAME = 'pgp_key'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY


class PGPKey(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.datetime.utcnow)
    seller_id = Column(Integer, ForeignKey(seller.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))
    key = Column(Text)
    key_hash = Column(CHAR(32))

    UniqueConstraint(seller_id, key_hash)

