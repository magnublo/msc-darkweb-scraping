from sqlalchemy import Column, Integer, String

from src.base import Base
TABLE_NAME = 'country'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Country(Base):

    __tablename__ = TABLE_NAME

    id = Column(PRIMARY_KEY, String, primary_key=True)
