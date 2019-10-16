from sqlalchemy import Column, CHAR

from definitions import COUNTRY_NAME_COLUMN_LENGTH, Base

TABLE_NAME = 'country'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Country(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, CHAR(COUNTRY_NAME_COLUMN_LENGTH), primary_key=True)
