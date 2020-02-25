import pickle
from collections import defaultdict
from datetime import datetime
from typing import Tuple

from definitions import ROOT_SRC_DIR
from src.models.listing_observation import ListingObservation

l: ListingObservation
with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/all_listings_prod_schema.pickle", "rb") as f:
    listings = [l for l in pickle.load(f) if l.url]


listing_tuples_by_url = defaultdict(list)
max_ids = set()

for l in listings:
    id_date_tuple = (l.id, l.created_date)
    listing_tuples_by_url[l.url].append(id_date_tuple)


for url in listing_tuples_by_url.keys():
    ids_and_dates = listing_tuples_by_url[url]
    max_id_and_date = max(ids_and_dates, key=lambda e: e[1])
    max_ids.add(max_id_and_date[0])

with open(f"{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/insert_most_recent_listing_observations.sql", "w") as f:
    joined_ids = ", ".join([str(i) for i in max_ids])
    f.write(f"INSERT INTO most_recent_listing_observation SELECT * FROM listing_observation WHERE id IN ({joined_ids});")
