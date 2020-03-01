import pickle
from collections import defaultdict

from definitions import ROOT_SRC_DIR
from src.db_data_scripts.analysis.parse_titles import get_all_titles_parsed_titles_and_parsed_titles_and_nr_of_grams
from src.db_data_scripts.utils import get_most_recent_listing_dump_file_path, \
    get_most_recent_listing_observation_category_dump_file_path
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory


all_titles, parsed_titles, parsed_titles_and_nr_of_grams = get_all_titles_parsed_titles_and_parsed_titles_and_nr_of_grams()
print(f"Got gram analysis from titles")

most_recent_listing_dump = get_most_recent_listing_dump_file_path()
most_recent_listing_observation_category_dump = get_most_recent_listing_observation_category_dump_file_path()

with open(most_recent_listing_dump, "rb") as f:
#with open("/home/magnus/PycharmProjects/msc/src/db_data_scripts/pickle_data/all_listings_subset.pickle", "rb") as f:
    l: ListingObservation
    listings = [l for l in pickle.load(f) if l.price is not None]
print(f"Loaded {len(listings)} listings")

with open(most_recent_listing_observation_category_dump, "rb") as f:
    c: ListingObservationCategory
    listing_observation_categories = [c for c in pickle.load(f)]

    listing_id_to_categori_id = defaultdict(list)

    for c in listing_observation_categories:
        listing_id_to_categori_id[c.listing_observation_id].append(c.category_id)

print(f"Loaded {len(listing_observation_categories)} category junctions")

drug_category_ids = (1, 136, 139, 141, 146, 151, 154, 159, 161, 210)
drug_listings = []

for l in listings:
    category_ids_for_listing = listing_id_to_categori_id.get(l.id)
    if category_ids_for_listing:
        for id in category_ids_for_listing:
            if id in drug_category_ids:
                drug_listings.append(l)

print(f"Mapped drug listings")

sql_values = []

for drug_listing in drug_listings:
    grams = parsed_titles_and_nr_of_grams.get(drug_listing.title)
    if grams is not None:
        sql_values.append(f"({drug_listing.id}, {grams})")

print(f"Generated SQL string. now writing to file...")

with open(f"{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/insert_grams_per_listing.sql", "w") as f:
    stmt = "INSERT into `listing_observation` (id, grams_per_unit) VALUES " + ",\n".join(sql_values) + "\nON DUPLICATE KEY UPDATE grams_per_unit = VALUES(grams_per_unit); "
    f.write(stmt)


# INSERT into `listing_observation` (id, grams_per_unit)
#     VALUES (1, 'apple'), (2, 'orange'), (3, 'peach')
#     ON DUPLICATE KEY UPDATE grams_per_unit = VALUES(grams_per_unit);
