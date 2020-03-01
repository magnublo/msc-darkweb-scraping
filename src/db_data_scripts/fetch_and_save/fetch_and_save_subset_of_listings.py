import pickle

from sqlalchemy import func

from definitions import ROOT_SRC_DIR
from src.db_utils import get_engine, get_db_session
from src.models.listing_observation import ListingObservation
from src.models.scraping_session import ScrapingSession

engine = get_engine()

db_session = get_db_session(engine)

listing_urls = [u[0] for u in db_session.query(ListingObservation.url).join(ScrapingSession, isouter=True).group_by(ListingObservation.url).having(func.count(ListingObservation.id) > 3).filter(ListingObservation.url != None, ScrapingSession.market=="CRYPTONIA_MARKET").limit(100).all()]

listings = db_session.query(ListingObservation).filter(ListingObservation.url.in_(listing_urls)).all()

print(f"fetched listings, {len(listings)}")
with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/all_listings_subset.pickle", "wb") as f:
    pickle.dump(listings, f)