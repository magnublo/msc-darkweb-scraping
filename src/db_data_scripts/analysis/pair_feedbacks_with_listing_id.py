import pickle
from typing import Dict, Tuple

from definitions import ROOT_SRC_DIR
from src.db_data_scripts.utils import get_most_recent_listing_dump_file_path, get_most_recent_feedback_dump_file_path
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation

most_recent_listing_dump = get_most_recent_listing_dump_file_path()
listings_by_seller_id_and_product_title: Dict[Tuple[int, str], ListingObservation] = {}
listings_by_url: Dict[str, ListingObservation] = {}
listings_by_title: Dict[str, ListingObservation] = {}

with open(most_recent_listing_dump, "rb") as f:
    listings = pickle.load(f)

print(f"Loaded {len(listings)} listings.")

l: ListingObservation
for l in listings:
    if l.title:
        listings_by_seller_id_and_product_title[(l.seller_id, l.title.strip())] = l
        listings_by_title[l.title] = l
    if l.url:
        listings_by_url[l.url] = l

print("Created mapping listings_by_seller_id_and_product_title")

most_recent_feedback_dump = get_most_recent_feedback_dump_file_path()

with open(most_recent_feedback_dump, "rb") as f:
    feedbacks = pickle.load(f)

print(f"Loaded {len(feedbacks)} feedbacks.")

sql_value_lines = []
f: Feedback
with open(f"{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/update_listing_id_on_feedbacks.sql",
          "w") as output_file:
    for feedback in feedbacks:
        corresponding_listing = None

        if feedback.product_url:
            corresponding_listing = listings_by_url.get(feedback.product_url)

        if not corresponding_listing:
            if feedback.product_title and feedback.seller_id is not None:
                corresponding_listing = listings_by_seller_id_and_product_title.get((feedback.seller_id, feedback.product_title.strip()))
                if not corresponding_listing:
                    corresponding_listing = listings_by_seller_id_and_product_title.get(
                        (feedback.seller_id, feedback.product_title))

        if not corresponding_listing:
            if feedback.product_title:
                corresponding_listing = listings_by_title.get(feedback.product_title.strip())
                if not corresponding_listing:
                    corresponding_listing = listings_by_title.get(feedback.product_title)

        if corresponding_listing:
            sql_value_lines.append(f"({feedback.id}, {corresponding_listing.id})")

    stmt = "INSERT into magnublo_scraping.`feedback` (id, listing_id) VALUES \n" + ",\n".join(
        sql_value_lines) + "\nON DUPLICATE KEY UPDATE listing_id = VALUES(listing_id); "

    output_file.write(stmt)

# UPDATE `magnublo_scraping`.`feedback` SET `listing_id` = '1' WHERE (`id` = '15');
