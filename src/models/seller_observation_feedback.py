from sqlalchemy import Column, String, ForeignKey, Integer

from src.base import Base
from src.models import seller_observation, feedback

TABLE_NAME = 'seller_observation_feedback'
SELLER_OBSERVATION_ID_NAME = 'seller_observation_id'
FEEDBACK_ID_NAME = 'feedback_id'

class SellerObservationFeedback(Base):

    __tablename__ = TABLE_NAME

    seller_observation_id = Column(SELLER_OBSERVATION_ID_NAME, Integer,
                                    ForeignKey(seller_observation.TABLE_NAME_AND_PRIMARY_KEY), primary_key=True)
    feedback_id = Column(FEEDBACK_ID_NAME, Integer, ForeignKey(feedback.TABLE_NAME_AND_PRIMARY_KEY), primary_key=True)
    product_url = Column(String)

