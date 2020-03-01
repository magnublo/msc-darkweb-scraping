import pickle
from typing import Dict, Tuple

from definitions import ROOT_SRC_DIR
from src.db_data_scripts.utils import get_most_recent_listing_dump_file_path
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation

destination_file = 1

most_recent_listing_dump = get_most_recent_listing_dump_file_path()
listings_by_url: Dict[str, ListingObservation] = {}
with open(most_recent_listing_dump, "rb") as f:
    listings = pickle.load(f)

print(f"Loaded {len(listings)} listings.")

l: ListingObservation
for l in listings:
    listings_by_url[l.url] = l

print("Created mapping listings_by_url")

with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/feedback_urls_where_product_title_is_none.pickle", "rb") as f:
    feedbacks_without_title = pickle.load(f)

print(f"Loaded {len(feedbacks_without_title)} listings.")

f: Feedback
with open(f"{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/update_listing_id_on_feedbacks_without_title.sql",
          "a") as output_file:
    for feedback in feedbacks_without_title:
        corresponding_listing = listings_by_url.get(f.product_url)
        if corresponding_listing:
            output_file.write(
                f"UPDATE `magnublo_scraping`.`feedback` SET `listing_id` = '{corresponding_listing.id}' WHERE (`id` = '{feedback.id}');\n")

# UPDATE `magnublo_scraping`.`feedback` SET `listing_id` = '1' WHERE (`id` = '15');
