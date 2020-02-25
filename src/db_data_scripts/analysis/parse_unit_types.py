import pickle
import re
from typing import Dict

from definitions import ROOT_SRC_DIR


from src.db_data_scripts.table_it import printTable
from src.utils import parse_float

unit_type_to_gram: Dict[str, float] = {}
parsed_unit_types = set()
all_unit_types = set()
parsed_types_and_nr_of_grams = []

with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/cryptonia_titles_and_unit_types.pickle", "rb") as f:
    titles_and_unit_types = [u for u in pickle.load(f) if u[0] and u[1]]


for title, unit_type in titles_and_unit_types:
    all_unit_types.add((title, unit_type))
    match = re.match(r"([0-9.,]*|[0-9]+\/[0-9])-?(g|grams|gram|gr)$", unit_type, flags=re.IGNORECASE)
    if match:
        start_index = match.regs[1][0]
        end_index = match.regs[1][1]
        numerical_expression = unit_type[start_index:end_index]
        if numerical_expression.find("/") != -1:
            # fraction
            numerator, denominator = [int(s) for s in numerical_expression.split("/")]
            grams = numerator / denominator
        else:
            # decimal
            numerical_expression = numerical_expression if numerical_expression else "1"
            grams = parse_float(numerical_expression)

        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(r"([0-9.,]*|[0-9]+\/[0-9])-?(mg|mgrams|mgram|milligrams|mgs)$", unit_type, flags=re.IGNORECASE)

    if match:
        start_index = match.regs[1][0]
        end_index = match.regs[1][1]
        numerical_expression = unit_type[start_index:end_index]
        if numerical_expression.find("/") != -1:
            # fraction
            numerator, denominator = [int(s) for s in numerical_expression.split("/")]
            grams = (numerator / denominator) * 0.001
        else:
            # decimal
            numerical_expression = numerical_expression if numerical_expression else "1"
            grams = parse_float(numerical_expression) * 0.001

        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(r"([0-9.,]*|[0-9]+\/[0-9])-?(kg|kgs|kilos|kilo|kilogram|kilograms)$", unit_type, flags=re.IGNORECASE)

    if match:
        start_index = match.regs[1][0]
        end_index = match.regs[1][1]
        numerical_expression = unit_type[start_index:end_index]
        if numerical_expression.find("/") != -1:
            # fraction
            numerator, denominator = [int(s) for s in numerical_expression.split("/")]
            grams = (numerator / denominator) * 1000
        else:
            # decimal
            numerical_expression = numerical_expression if numerical_expression else "1"
            grams = parse_float(numerical_expression) * 1000

        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(r"([0-9.,]*|[0-9]+\/[0-9])-?(mcg|mcgs|ug|ugs|μgs|μg|microgram|microg)$", unit_type,
                     flags=re.IGNORECASE)

    if match:
        start_index = match.regs[1][0]
        end_index = match.regs[1][1]
        numerical_expression = unit_type[start_index:end_index]
        if numerical_expression.find("/") != -1:
            # fraction
            numerator, denominator = [int(s) for s in numerical_expression.split("/")]
            grams = (numerator / denominator) * 1000
        else:
            # decimal
            numerical_expression = numerical_expression if numerical_expression else "1"
            grams = parse_float(numerical_expression) * 1000

        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

unparsed_unit_types = all_unit_types.difference(parsed_unit_types)
printTable(list([(s[1], s[0]) for s in unparsed_unit_types]))
printTable(parsed_types_and_nr_of_grams)
#print("\n".join(["\t\t\t\t\t\t".join(s) for s in unparsed_unit_types]))

# UPDATE `magnublo_scraping`.`listing_observation` SET `is_weight_unit_type` = '1', `grams_per_unit` = '5' WHERE (`id` = '16');