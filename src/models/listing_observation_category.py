from sqlalchemy import Column, ForeignKey, Integer

import src.models.listing_category as listing_category
import src.models.listing_observation as listing_observation
from definitions import Base, MYSQL_CASCADE

TABLE_NAME = 'listing_observation_category'
LISTING_OBSERVATION_ID_NAME = 'listing_observation_id'
CATEGORY_ID_NAME = 'category_id'

class ListingObservationCategory(Base):

    __tablename__ = TABLE_NAME

    listing_observation_id = Column(LISTING_OBSERVATION_ID_NAME, Integer,
                                    ForeignKey(listing_observation.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE),
                                    primary_key=True)

    category_id = Column(CATEGORY_ID_NAME, Integer, ForeignKey(listing_category.TABLE_NAME_AND_PRIMARY_KEY, ondelete=MYSQL_CASCADE),
                         primary_key=True)
