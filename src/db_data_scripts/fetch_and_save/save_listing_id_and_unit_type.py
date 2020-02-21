import pickle

from definitions import ROOT_SRC_DIR
from src.models.listing_observation import ListingObservation


class ListingIdTitleAndUnitType:

    def __init__(self, id: int, unit_type: str, title: str):
        self.id = id
        self.unit_type = unit_type
        self.title = title


unit_types = set()

with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/all_listings.pickle", "rb") as f:
    listings = pickle.load(f)

print(f"Loaded {len(listings)} listings.")

ids_titles_and_unit_types = []
l: ListingObservation

for l in listings:
    listing_id_and_unit_type = ListingIdTitleAndUnitType(l.id, l.unit_type, l.title)
    ids_titles_and_unit_types.append(listing_id_and_unit_type)

with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/listing_ids_titles_and_unit_types.pickle", "wb") as f:
    pickle.dump(ids_titles_and_unit_types, f)

# UPDATE `magnublo_scraping`.`listing_observation` SET `is_weight_unit_type` = '1', `grams_per_unit` = '5' WHERE (`id` = '16');