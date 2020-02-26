import pickle
import re
from typing import Dict

from text2digits import text2digits

from definitions import ROOT_SRC_DIR


from src.db_data_scripts.table_it import printTable
from src.utils import parse_float

unit_type_to_gram: Dict[str, float] = {}
parsed_unit_types = set()
all_unit_types = set()
parsed_types_and_nr_of_grams = []

WORD_NUMBERS_REGEX_PART = "half|quarter|eighth|third|quarter|fifth|sixth|seventh|ninth"
BASE_REGEX = r"`?(" + WORD_NUMBERS_REGEX_PART + r"|[0-9.,]+(?:x|\*)[0-9.,]+|[0-9.,]*|[0-9]+\/[0-9])-?"
GRAM_REGEX = BASE_REGEX + r"(g|grams|gram|gr|gramm|gramms)$"
MILLIGRAM_REGEX = BASE_REGEX + r"(mg|mgrams|mgram|milligrams|mgs)$"
MICROGRAM_REGEX = BASE_REGEX + r"(mcg|mcgs|ug|ugs|μgs|μg|microgram|microg)$"
KILOGRAM_REGEX = BASE_REGEX + r"(kg|kgs|kilos|kilo|kilogram|kilograms)$"
POUND_REGEX = BASE_REGEX + r"(pound|lb|lbs|pounds)$"


def convert_to_number(numerical_expression) -> float:
    lower_numerical_expression = numerical_expression.lower()
    if lower_numerical_expression == "half":
        return 1/2
    elif lower_numerical_expression == "third":
        return 1/3
    elif lower_numerical_expression == "quarter":
        return 1/4
    elif lower_numerical_expression == "fifth":
        return 1/5
    elif lower_numerical_expression == "sixth":
        return 1/6
    elif lower_numerical_expression == "seventh":
        return 1/7
    elif lower_numerical_expression == "eighth":
        return 1/8
    elif lower_numerical_expression == "ninth":
        return 1/9
    else:
        return float(text2digits.Text2Digits().convert_to_digits(str(numerical_expression)))


def get_grams(unit_type: str, match: re.Match, grams_per_unit: float):
    start_index = match.regs[1][0]
    end_index = match.regs[1][1]
    numerical_expression = unit_type[start_index:end_index]
    if numerical_expression.find("/") != -1:
        # fraction
        numerator, denominator = [int(s) for s in numerical_expression.split("/")]
        grams = (numerator / denominator) * grams_per_unit
    elif numerical_expression.find("*") != -1 or numerical_expression.find("x") != -1:
        # product
        factor_one, factor_two = [float(s) for s in re.split(r"\*|x", numerical_expression)]
        grams = (factor_one * factor_two) * grams_per_unit
    elif re.search(WORD_NUMBERS_REGEX_PART, numerical_expression, flags=re.IGNORECASE):
        grams = float(convert_to_number(str(numerical_expression))) * grams_per_unit
    else:
        # decimal
        numerical_expression = numerical_expression if numerical_expression else "1"
        grams = parse_float(numerical_expression) * grams_per_unit

    return grams


with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/cryptonia_titles_and_unit_types.pickle", "rb") as f:
    titles_and_unit_types = [u for u in pickle.load(f) if u[0] and u[1]]


for title, unit_type in titles_and_unit_types:
    all_unit_types.add((title, unit_type))

    match = re.match(GRAM_REGEX, unit_type, flags=re.IGNORECASE)
    if match:
        grams = get_grams(unit_type, match, grams_per_unit=1)
        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(MILLIGRAM_REGEX, unit_type, flags=re.IGNORECASE)

    if match:
        grams = get_grams(unit_type, match, grams_per_unit=10**-3)
        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(KILOGRAM_REGEX, unit_type, flags=re.IGNORECASE)

    if match:
        grams = get_grams(unit_type, match, grams_per_unit=10**3)
        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(MICROGRAM_REGEX, unit_type,
                     flags=re.IGNORECASE)

    if match:
        grams = get_grams(unit_type, match, grams_per_unit=10**-6)
        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

    match = re.match(POUND_REGEX, unit_type,
                     flags=re.IGNORECASE)

    if match:
        grams = get_grams(unit_type, match, grams_per_unit=453.592)
        parsed_unit_types.add((title, unit_type))
        parsed_types_and_nr_of_grams.append((unit_type, str(grams)))
        continue

unparsed_unit_types = all_unit_types.difference(parsed_unit_types)
printTable(list([(s[1], s[0]) for s in unparsed_unit_types]))
printTable(parsed_types_and_nr_of_grams)
#print("\n".join(["\t\t\t\t\t\t".join(s) for s in unparsed_unit_types]))
#print("\n".join([p[1] for p in unparsed_unit_types]))
print(len(parsed_unit_types)/len(all_unit_types))
# UPDATE `magnublo_scraping`.`listing_observation` SET `is_weight_unit_type` = '1', `grams_per_unit` = '5' WHERE (`id` = '16');