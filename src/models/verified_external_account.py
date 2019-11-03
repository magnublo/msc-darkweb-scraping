from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy import Float, CHAR

from definitions import Base, MARKET_NAME_COLUMN_LENGTH, MYSQL_CASCADE, MYSQL_VARCHAR_DEFAULT_LENGTH
from src.models import seller_observation

TABLE_NAME = 'verified_external_account'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME + "." + PRIMARY_KEY


class VerifiedExternalAccount(Base):
    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    seller_observation_id = Column(Integer,
                                   ForeignKey(seller_observation.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))

    market_id = Column(CHAR(MARKET_NAME_COLUMN_LENGTH))
    confirmed_sales = Column(Integer)
    rating = Column(Float)
    max_rating = Column(Float)

    nr_of_good_reviews = Column(Integer)
    nr_of_neutral_reviews = Column(Integer)
    nr_of_bad_reviews = Column(Integer)

    free_text = Column(String(MYSQL_VARCHAR_DEFAULT_LENGTH))
