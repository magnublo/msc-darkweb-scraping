import pickle

from definitions import CRYPTONIA_MARKET_ID, ROOT_SRC_DIR
from src.db_data_scripts.utils import get_most_recent_feedback_dump_file_path, get_most_recent_listing_dump_file_path
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation

most_recent_listing_dump = get_most_recent_listing_dump_file_path()
most_recent_feedback_dump = get_most_recent_feedback_dump_file_path()

with open(most_recent_listing_dump, "rb") as f:
    listings = pickle.load(f)

id_to_listing = {}

for l in listings:
    id_to_listing[l.id] = l

print(f"Loaded {len(listings)} listings from {most_recent_listing_dump}.")


with open(most_recent_feedback_dump, "rb") as f:
    feedbacks = pickle.load(f)

print(f"Loaded {len(feedbacks)} feedbacks from {most_recent_feedback_dump}.")


sql_value_lines = []

listing: ListingObservation
f: Feedback
for f in feedbacks:
    listing = id_to_listing.get(f.listing_id)
    if listing is not None and listing.price is not None and f.price is not None and f.market != CRYPTONIA_MARKET_ID and listing.price > 0.011 and f.price != 0:
        rounded_nr_of_units = int(round(f.price / listing.price))
        sql_value_lines.append(f"({f.id}, {rounded_nr_of_units})")

stmt = "INSERT into magnublo_scraping.`feedback` (id, units_bought) VALUES \n" + ",\n".join(
    sql_value_lines) + "\nON DUPLICATE KEY UPDATE units_bought = VALUES(units_bought); "


with open(f"{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/insert_units_bought_statement.sql", "w") as file:
    file.write(stmt)