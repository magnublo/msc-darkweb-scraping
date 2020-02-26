from src.db_utils import get_engine, get_db_session
from src.models.listing_observation import ListingObservation

db_engine = get_engine()
db_session = get_db_session(db_engine)

all_listings = db_session.query(ListingObservation)