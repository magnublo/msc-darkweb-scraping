import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, CHAR, UniqueConstraint

from definitions import MYSQL_CASCADE, Base, COUNTRY_NAME_COLUMN_LENGTH
from src.models import country

TABLE_NAME = 'country_alias'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class CountryAlias(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    name = Column(CHAR(COUNTRY_NAME_COLUMN_LENGTH))
    country_id = Column(Integer, ForeignKey(country.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE))

    UniqueConstraint(name)

