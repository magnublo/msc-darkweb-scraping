from sqlalchemy import Column, String, ForeignKey, Integer

import src.models.country as country
import src.models.listing_observation as listing_observation
from src.main import Base

TABLE_NAME = 'listing_observation_country'
LISTING_OBSERVATION_ID_NAME = 'listing_observation_id'
COUNTRY_ID_NAME = 'country_id'

class ListingObservationCountry(Base):

    __tablename__ = TABLE_NAME

    listing_observation_id = Column(LISTING_OBSERVATION_ID_NAME, Integer,
                                    ForeignKey(listing_observation.TABLE_NAME_AND_PRIMARY_KEY), primary_key=True)
    country_id = Column(COUNTRY_ID_NAME, String, ForeignKey(country.TABLE_NAME_AND_PRIMARY_KEY), primary_key=True)
