import pickle
import re
from typing import Dict, Set, Tuple, List

from text2digits import text2digits

from definitions import ROOT_SRC_DIR
from src import utils

from src.db_data_scripts.table_it import printTable


parsed_titles = set()

WORD_NUMBERS_REGEX_PART = "half|quarter|eighth|third|quarter|fifth|sixth|seventh|ninth|"
WORD_NUMBERS_REGEX = "(half|quarter|eighth|third|quarter|fifth|sixth|seventh|ninth)"

GRAM_EXPRESSIONS = "g", "grams", "gram", "gr", "gramm", "gramms"
MILLIGRAM_EXPRESSIONS = "mg", "mgrams", "mgram", "mgr", "mgramm", "mgramms", "millig", "milligrams", "milligram", "milligr", "milligramm", "milligramms", "мg", "мgraмs", "мgraм", "мgr", "мgraмм", "мgraммs", "мillig", "мilligraмs", "мilligraм", "мilligr", "мilligraмм", "мilligraммs"


# NB! µ and μ are different characters
MICROGRAM_EXPRESSIONS = "mcg", "mcgs", "ug", "ugs", "μgs", "μg", "microgram", "microg", "µg", "µgs"
KILOGRAM_EXPRESSIONS = "kg", "kgs", "kilos", "kilo", "kilogram", "kilograms", "kgrams"
POUND_EXPRESSIONS = "pound", "lb", "lbs", "pounds"
OUNCE_EXPRESSIONS = "ounce", "ounces", "oz"

EXTRA_UNWANTED_POSTFIXES_TO_UNIT_EXPRESSION = "euro", "oz", "customer", "eu", "each", "gbp", r"\$", "£", "€", "percent", "%"
UNWANTED_POSTFIXES_TO_UNIT_EXPRESSION = GRAM_EXPRESSIONS + MILLIGRAM_EXPRESSIONS + MICROGRAM_EXPRESSIONS + KILOGRAM_EXPRESSIONS + POUND_EXPRESSIONS + OUNCE_EXPRESSIONS + EXTRA_UNWANTED_POSTFIXES_TO_UNIT_EXPRESSION

EXCLUSION_LIST = "".join([f"(?!{s})" for s in UNWANTED_POSTFIXES_TO_UNIT_EXPRESSION])

ALL_MASS_EXPRESSIONS = list(GRAM_EXPRESSIONS+MILLIGRAM_EXPRESSIONS+MICROGRAM_EXPRESSIONS+KILOGRAM_EXPRESSIONS+POUND_EXPRESSIONS+OUNCE_EXPRESSIONS)
ALL_MASS_EXPRESSIONS.sort(key=lambda l: len(l), reverse=True)

MASS_REGEX = r"(?:^|(?!$[0-9]+))" + r"(" + WORD_NUMBERS_REGEX_PART + r"[0-9]+|[0-9]+,[0-9]+|(?:[0-9]*\.[0-9,]+)|[0-9]\/[0-9])(?:\s|-|full)*(" + r"|".join(ALL_MASS_EXPRESSIONS) + r")"
NUMBER_OF_UNITS_REGEX = r"(?:^|\s|x)[^€$£#A-z0-9]{0,}([0-9]+|[0-9]+,[0-9]+|(?:\(|\[)?[0-9]+(?:\)|\])?|$)(?:\s+|x|abs|!|pcs)(?:" + EXCLUSION_LIST + ")"

def parse_float(f: str) -> float:
    number_of_dots = len([m.start() for m in re.finditer(r"\.", f)])
    f = f.replace(".", "", number_of_dots-1)
    return utils.parse_float(f)

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


def get_grams_per_mass_unit(title: str, mass_match: re.Match) -> float:
    start_index = mass_match.regs[2][0]
    end_index = mass_match.regs[2][1]
    type_of_mass_unit = title[start_index:end_index].lower()
    if type_of_mass_unit in GRAM_EXPRESSIONS:
        return 1
    elif type_of_mass_unit in MILLIGRAM_EXPRESSIONS:
        return 10**-3
    elif type_of_mass_unit in MICROGRAM_EXPRESSIONS:
        return 10**-6
    elif type_of_mass_unit in KILOGRAM_EXPRESSIONS:
        return 10**3
    elif type_of_mass_unit in POUND_EXPRESSIONS:
        return 453.592
    elif type_of_mass_unit in OUNCE_EXPRESSIONS:
        return 28.3495
    else:
        raise AssertionError


def get_nr_of_mass_units(title: str, match: re.Match) -> float:
    start_index = match.regs[1][0]
    end_index = match.regs[1][1]
    numerical_expression = title[start_index:end_index]
    if numerical_expression.find("/") != -1:
        # fraction
        numerator, denominator = [int(s) for s in numerical_expression.split("/")]
        nr_of_mass_units = (numerator / denominator)
    elif numerical_expression.find("*") != -1 or numerical_expression.find("x") != -1:
        # product
        factor_one, factor_two = [float(s) for s in re.split(r"\*|x", numerical_expression)]
        nr_of_mass_units = (factor_one * factor_two)
    else:
        word_match = re.search(WORD_NUMBERS_REGEX, numerical_expression, flags=re.IGNORECASE)
        if word_match:
            numerical_expression = word_match.string
            return float(convert_to_number(str(numerical_expression)))
        # decimal
        numerical_expression = numerical_expression if numerical_expression else "1"
        nr_of_mass_units = parse_float(numerical_expression)

    return nr_of_mass_units

def get_titles() -> Set[str]:
    with open(f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/unique_titles.pickle", "rb") as f:
        titles = pickle.load(f)
    return titles


all_titles = set([l for l in list(get_titles()) if l is not None])
parsed_titles_and_nr_of_grams: List[Tuple[str, str]] = []


def expression_is_blacklisted(nr_of_units: float, title: str) -> bool:
    return title.lower().find(f"first {int(nr_of_units)}") != -1


for title in all_titles:
    if title is None:
        continue
    unit_match = re.search(NUMBER_OF_UNITS_REGEX, title, flags=re.IGNORECASE)
    if unit_match:
        start_index = unit_match.regs[1][0]
        end_index = unit_match.regs[1][1]
        nr_of_units_expression = title[start_index:end_index].lower()
        nr_of_units = parse_float(nr_of_units_expression)
        if expression_is_blacklisted(nr_of_units, title):
            nr_of_units = 1
    else:
        nr_of_units = 1

    mass_match = re.search(MASS_REGEX, title, flags=re.IGNORECASE)
    if mass_match:
        nr_mass_units = get_nr_of_mass_units(title, mass_match)
        grams_per_mass_unit = get_grams_per_mass_unit(title, mass_match)
        nr_of_grams = nr_mass_units * grams_per_mass_unit * nr_of_units

        parsed_titles.add(title)
        parsed_titles_and_nr_of_grams.append((title[:80], str(nr_of_grams)))
        continue



unparsed_titles = all_titles.difference(parsed_titles)
print("\n".join(list(unparsed_titles)))
parsed_list_for_print = list(parsed_titles_and_nr_of_grams)
parsed_list_for_print.sort(key=lambda x: x[0])
#printTable(parsed_list_for_print)
#print("\n".join(["\t\t\t\t\t\t".join(s) for s in unparsed_unit_types]))
#print("\n".join([p[1] for p in unparsed_unit_types]))
print(len(parsed_titles) / len(all_titles))
# UPDATE `magnublo_scraping`.`listing_observation` SET       `is_weight_unit_type` = '1', `grams_per_unit` = '5' WHERE (`id` = '16');