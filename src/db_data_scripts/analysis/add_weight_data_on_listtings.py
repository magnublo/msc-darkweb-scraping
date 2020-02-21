import pickle
from typing import Dict
from definitions import ROOT_SRC_DIR
from src.db_data_scripts.fetch_and_save.save_listing_id_and_unit_type import ListingIdTitleAndUnitType
from src.models.listing_observation import ListingObservation

unit_types = set()


with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/listing_ids_titles_and_unit_types.pickle", "rb") as f:
    listings = pickle.load(f)

print(f"Loaded {len(listings)} listings.")

l: ListingIdTitleAndUnitType
for l in listings:
    unit_types.add(l.unit_type)

print(len(unit_types))

# UPDATE `magnublo_scraping`.`listing_observation` SET `is_weight_unit_type` = '1', `grams_per_unit` = '5' WHERE (`id` = '16');