import pickle
from datetime import date

from definitions import ROOT_SRC_DIR
from environment_settings import DB_HOST, DB_NAME
from src.db_utils import get_engine, get_db_session
from src.models.listing_observation import ListingObservation

engine = get_engine()

db_session = get_db_session(engine)

today = date.today()
date_str = f"{str(today.day).zfill(2)}-{str(today.month).zfill(2)}-{str(today.year).zfill(2)}"
listings = db_session.query(ListingObservation).all()

print(f"fetched listings, {len(listings)}")
with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/{DB_HOST}__{DB_NAME}__{date_str}__all_listings.pickle", "wb") as f:
    pickle.dump(listings, f)