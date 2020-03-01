import pickle
from datetime import date

from definitions import ROOT_SRC_DIR
from environment_settings import DB_HOST, DB_NAME
from src.db_utils import get_engine, get_db_session
from src.models.listing_category import ListingCategory
from src.models.listing_observation_category import ListingObservationCategory

engine = get_engine()

db_session = get_db_session(engine)

today = date.today()
date_str = f"{str(today.day).zfill(2)}-{str(today.month).zfill(2)}-{str(today.year).zfill(2)}"
categories = db_session.query(ListingCategory).all()

print(f"fetched categories, {len(categories)}")
with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/{DB_HOST}__{DB_NAME}__{date_str}__all_listing_category.pickle", "wb") as f:
    pickle.dump(categories, f)