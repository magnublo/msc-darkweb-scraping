import pickle
import re
from typing import Dict

from definitions import ROOT_SRC_DIR

unit_type_to_gram: Dict[str, float] = {}
parsed_unit_types = set()

with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/cryptonia_unit_types.pickle", "rb") as f:
    unit_types = pickle.load(f)

for unit_type in unit_types:
    match = re.match(r"([0-9]+)g", unit_type, flags=re.IGNORECASE)
    if match:
        parsed_unit_types.add(unit_type)
        start
        grams = match.regs
        a = 0

# UPDATE `magnublo_scraping`.`listing_observation` SET `is_weight_unit_type` = '1', `grams_per_unit` = '5' WHERE (`id` = '16');