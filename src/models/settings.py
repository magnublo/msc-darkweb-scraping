from sqlalchemy import Column, Integer, Boolean

from definitions import Base

TABLE_NAME = 'settings'
PRIMARY_KEY = 'id'
TABLE_NAME_AND_PRIMARY_KEY = TABLE_NAME+"."+PRIMARY_KEY

class Settings(Base):

    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    refill_queue_when_complete = Column(Boolean)

