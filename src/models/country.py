import uuid

from sqlalchemy import Column, CHAR, Integer, UniqueConstraint, Index, Boolean

from definitions import COUNTRY_NAME_COLUMN_LENGTH, Base

TABLE_NAME = 'country'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Country(Base):

    __tablename__ = TABLE_NAME
    # TODO: Make __init__ that converts id to standardized name
    id = Column(PRIMARY_KEY, Integer, primary_key=True)
    name = Column(CHAR(COUNTRY_NAME_COLUMN_LENGTH))
    iso_alpha2_code = Column(CHAR(2))
    iso_alpha3_code = Column(CHAR(3))
    is_continent = Column(Boolean)

    UniqueConstraint(name)
    Index(uuid.uuid4(), iso_alpha2_code)
    Index(uuid.uuid4(), iso_alpha3_code)
