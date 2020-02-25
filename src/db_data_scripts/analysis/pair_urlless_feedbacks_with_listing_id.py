import pickle
from typing import Dict, Tuple

from definitions import ROOT_SRC_DIR
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation

destination_file = 1

listings_by_seller_id_and_product_title: Dict[Tuple[int, str], ListingObservation] = {}
with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/all_listings.pickle", "rb") as f:
    listings = pickle.load(f)

print(f"Loaded {len(listings)} listings.")

l: ListingObservation
for l in listings:
    if l.title:
        listings_by_seller_id_and_product_title[(l.seller_id, l.title.strip())] = l

print("Created mapping listings_by_seller_id_and_product_title")

with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/feedbacks_where_url_is_none.pickle", "rb") as f:
    feedbacks_without_url = pickle.load(f)

print(f"Loaded {len(feedbacks_without_url)} listings.")

f: Feedback
with open(f"{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/update_listing_id_on_feedbacks.sql",
          "a") as output_file:
    for feedback in feedbacks_without_url:
        corresponding_listing = listings_by_seller_id_and_product_title.get((feedback.seller_id, feedback.product_title.strip()))
        if corresponding_listing:
            output_file.write(
                f"UPDATE `magnublo_scraping`.`feedback` SET `listing_id` = '{corresponding_listing.id}' WHERE (`id` = '{feedback.id}');\n")

# UPDATE `magnublo_scraping`.`feedback` SET `listing_id` = '1' WHERE (`id` = '15');
