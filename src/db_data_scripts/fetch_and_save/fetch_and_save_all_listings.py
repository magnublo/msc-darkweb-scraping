import pickle

from definitions import ROOT_SRC_DIR
from src.db_utils import get_engine, get_db_session
from src.models.listing_observation import ListingObservation

engine = get_engine()

db_session = get_db_session(engine)

listings = db_session.query(ListingObservation).all()

print(f"fetched listings, {len(listings)}")
with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/all_listings.pickle", "wb") as f:
    pickle.dump(listings, f)