import multiprocessing
import pickle
import re
import statistics
import sys
from datetime import datetime
from decimal import getcontext, Decimal, DivisionUndefined, InvalidOperation
from itertools import islice
from multiprocessing import Queue
from time import sleep
from typing import List, Dict, Tuple, Optional

import numpy
from sortedcontainers import SortedDict
from sqlalchemy.orm import Session

from definitions import ROOT_SRC_DIR
from src.db_utils import get_engine, get_db_session
from src.models.listing_observation import ListingObservation

getcontext().prec = 100

MAX_VALID_PERCENT_CHANGE = 25
FILE_PATHS = (
        "/home/magnus/PycharmProjects/msc/src/csv_data/ExchangeRates_25022020_early_hour.csv",
        "/home/magnus/PycharmProjects/msc/src/csv_data/ExchangeRates_25022020_early_minute.csv",
        "/home/magnus/PycharmProjects/msc/src/csv_data/ExchangeRates_25022020_late_hour.csv",
        "/home/magnus/PycharmProjects/msc/src/csv_data/ExchangeRates_25022020_late_minute.csv"
        )


def remove_leading_delimiter(curr) -> str:
    while curr and curr[0] == ";":
        curr = curr[1:]

    return curr


def get_currency_dictionaries():
    usd_percad_dict: SortedDict = SortedDict({})
    usd_per_aud_dict: SortedDict = SortedDict({})
    usd_per_gbp_dict: SortedDict = SortedDict({})
    usd_per_eur_dict: SortedDict = SortedDict({})

    for path in FILE_PATHS:
        with open(path, 'r') as file:
            rate_lines = file.readlines()[6:]

        for i, line in enumerate(rate_lines):

            a = line.split(";")
            eur_time, eur_rate, gbp_time, gbp_rate, cad_time, cad_rate, aud_time, aud_rate, _, _, _, _, _, _ = (line.split(";") + [None] * 2) [:14]

            for time_str, rate_str, usd_per_x_dict in zip((eur_time, gbp_time, cad_time, aud_time), (eur_rate, gbp_rate, cad_rate, aud_rate),
                                            (usd_per_eur_dict, usd_per_gbp_dict, usd_percad_dict, usd_per_aud_dict)):

                if not time_str:
                    continue

                month, day, year, hour, minute, second = ([int(t) for t in re.split(r"[\/\s:]", time_str)] + [0]*3)[:6]
                year = year + 2000 if year < 2000 else year
                if rate_str == cad_rate:
                    price = 1/float(rate_str)
                else:
                    price = float(rate_str)
                d = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second).timestamp()
                usd_per_x_dict[d] = price

    return usd_per_eur_dict, usd_per_gbp_dict, usd_percad_dict, usd_per_aud_dict



res = {}


def get_usd_rates(line):
    pass

def get_listing_observations() -> List[tuple]:
    with open("/home/magnus/PycharmProjects/msc/src/db_data_scripts/pickle_data/all_listings_prod_schema.pickle", "rb") as f:
        all_listing_observations: Tuple[ListingObservation] = pickle.load(f)


    listing_tuples = [(l.id, l.url, l.created_date, l.price, l.fiat_currency, l.btc_rate, l.xmr_rate, l.ltc_rate) for l in all_listing_observations if l.btc_rate and l.price]

    return listing_tuples


def get_listings_by_url(results: List[tuple]) -> Dict[str, List[tuple]]:
    url_dict = {}
    for id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate in results:
        if url not in url_dict.keys():
            url_dict[url] = [(id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate)]
        else:
            url_dict[url].append((id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate))

    return url_dict


def closest(sorted_dict, key):
    "Return closest key in `sorted_dict` to given `key`."
    assert len(sorted_dict) > 0
    keys = list(islice(sorted_dict.irange(minimum=key), 1))
    keys.extend(islice(sorted_dict.irange(maximum=key, reverse=True), 1))
    return min(keys, key=lambda k: abs(key - k))


def get_rate(usd_per_x_dict: SortedDict, date_time: datetime) -> Decimal:
    t = date_time.timestamp()
    closest_timestamp = closest(usd_per_x_dict, t)
    rate = usd_per_x_dict[closest_timestamp]
    return Decimal(rate)


def get_currency_variances(listing_observations: List[Tuple], rate_dicts: Tuple[SortedDict]) -> Optional[Tuple]:
    btcs: List[Decimal]
    xmrs: List[Decimal]
    ltcs: List[Decimal]
    usds: List[Decimal]
    cads: List[Decimal]
    auds: List[Decimal]
    gbps: List[Decimal]
    eurs: List[Decimal]
    arrs = btcs, xmrs, ltcs, usds, cads, auds, gbps, eurs = ([], [], [], [], [], [], [], [])
    # id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate
    # cleaned_listing_observations = [l for l in listing_observations if l[5] is not None]
    listing = listing_observations[0]
    usd_per_eur_dict, usd_per_gbp_dict, usd_per_cad_dict, usd_per_aud_dict = rate_dicts
    _, url, date_time, usd_price, _, usd_per_btc, usd_per_xmr, usd_per_ltc = listing
    usd_price, usd_per_btc, usd_per_xmr, usd_per_ltc = [d if d is None else Decimal(d) for d in
                                                        (usd_price, usd_per_btc, usd_per_xmr, usd_per_ltc)]
    base_btc = usd_price / usd_per_btc
    base_xmr = usd_price / usd_per_xmr
    base_ltc = usd_price / usd_per_ltc if usd_per_ltc else None
    # base_bch = usd_price / usd_per_bch if usd_per_bch else None
    base_cad = usd_price / get_rate(usd_per_cad_dict, date_time)
    base_aud = usd_price / get_rate(usd_per_aud_dict, date_time)
    base_gbp = usd_price / get_rate(usd_per_gbp_dict, date_time)
    base_eur = usd_price / get_rate(usd_per_eur_dict, date_time)
    base_usd = usd_price

    for listing in listing_observations:
        _, url, date_time, usd_price, _, usd_per_btc, usd_per_xmr, usd_per_ltc = listing
        usd_price, usd_per_btc, usd_per_xmr, usd_per_ltc = [d if d is None else Decimal(d) for d in
                                                        (usd_price, usd_per_btc, usd_per_xmr, usd_per_ltc)]
        if usd_price is None or usd_per_btc is None or base_btc is 0 or usd_per_btc is 0:
            continue
        try:
            btcs.append((usd_price / usd_per_btc) / base_btc)
            xmrs.append((usd_price / usd_per_xmr) / base_xmr)
            cads.append((usd_price / get_rate(usd_per_cad_dict, date_time)) / base_cad)
            auds.append((usd_price / get_rate(usd_per_aud_dict, date_time)) / base_aud)
            gbps.append((usd_price / get_rate(usd_per_gbp_dict, date_time)) / base_gbp)
            eurs.append((usd_price / get_rate(usd_per_eur_dict, date_time)) / base_eur)
            usds.append(usd_price / base_usd)
        except (DivisionUndefined, InvalidOperation):
            continue
        if base_ltc:
            ltcs.append((usd_price / usd_per_ltc) / base_ltc)
        else:
            ltcs.append(1)

    is_valid = len(usds) > 1
    for i in range(1, len(usds)):
        is_valid = is_valid and usds[i] / usds[i - 1] < (1 + MAX_VALID_PERCENT_CHANGE / 100) and usds[i] / usds[
            i - 1] > (1 - MAX_VALID_PERCENT_CHANGE / 100)

    return tuple([(n, statistics.variance(t)) for t, n in
                  zip(arrs, ('BTC', 'XMR', 'LTC', 'USD', 'CAD', 'AUD', 'GBP', 'EUR'))]) if is_valid else None


def get_line(url, underlying, min_var, second_min_var, n, btc_var, xmr_var, ltc_var, usd_var, cad_var, aud_var, gbp_var,
             eur_var) -> str:
    btc_var, xmr_var, ltc_var, usd_var, cad_var, aud_var, gbp_var, eur_var = [numpy.format_float_positional(a) for a in
                                                                              (btc_var[1], xmr_var[1], ltc_var[1],
                                                                               usd_var[1], cad_var[1], aud_var[1],
                                                                               gbp_var[1], eur_var[1])]
    return f"('{url}', '{underlying}', {numpy.format_float_positional(-(min_var-second_min_var))}, {btc_var}, " \
           f"{xmr_var}, {ltc_var}, {usd_var}, {cad_var}, " \
           f"{aud_var}, {gbp_var}, {eur_var}, {n}), \n"


def chunkify(lst, n):
    return [tuple(lst[i::n]) for i in range(n)]


def generate_lines(url_dict: dict, keys: Tuple[str], queue: Queue, t, rate_dicts: Tuple[SortedDict]):
    for i, url in enumerate(keys):
        l = len(keys)
        vars = get_currency_variances(url_dict[url], rate_dicts)
        if vars is not None:
            min_var, second_min_var = sorted(vars, key=lambda v: v[1])[0:2]
            queue.put(get_line(url, min_var[0], min_var[1], second_min_var[1], len(url_dict[url]), *vars))

        if i % 20000 == 0:
            sys.stdout.write(f"\r{t} {round(i/len(keys), 2)*100} %")
            sys.stdout.flush()
    exit(0)


queue = multiprocessing.Queue()
rate_dicts = get_currency_dictionaries()

# assert USD_PER_CAD_DICT.keys() == USD_PER_AUD_DICT.keys() == USD_PER_GBP_DICT.keys() == USD_PER_EUR_DICT.keys()

listings = get_listing_observations()
url_dict = get_listings_by_url(listings)

nr_of_threads = 12
keys = [k for k in url_dict.keys()]
i = 0
ts = []

for chunk in chunkify(keys, nr_of_threads):
    new_dict = {}
    for k in chunk:
        new_dict[k] = url_dict[k]
    t = multiprocessing.Process(target=generate_lines, args=(new_dict, chunk, queue, i, rate_dicts))
    ts.append(t)
    t.start()
    i += 1

while True:
    s = queue.qsize()
    sleep(1)
    s2 = queue.qsize()
    if s == s2: break
print("Threads were joined.")

sql_lines = []

while not queue.empty():
    sql_lines.append(queue.get())

with open(f'{ROOT_SRC_DIR}/db_data_scripts/generated_sql_statements/insert_variances_statement.sql', 'w') as f:
    f.write(
        r'INSERT INTO `magnublo_scraping`.`listing_observation_currency_variances` (`url`, `underlying`, '
        r'`next_best_diff`, `btc_var`, `xmr_var`, `ltc_var`, `usd_var`, `cad_var`, `aud_var`, `gbp_var`, '
        r'`eur_var`, '
        r'`nr_of_observations`) '
        r'VALUES ')
    # noinspection SqlNoDataSourceInspection,SqlResolve
    f.writelines(sql_lines[:-1])
    f.write(sql_lines[-1].strip()[:-1])


# INSERT INTO `magnublo_scraping`.`listing_observation_currency_variances` (`listing_observation_id`, `min_var`,
# `next_best_diff`, `btc_var`, `xmr_var`, `ltc_var`, `usd_var`, `cad_var`, `aud_var`, `gbp_var`, `eur_var`,
# `min_var`) VALUES ('1', '8.9', '0.8', '0.9', '0.78', '0.6', '0.45', '0.3', '0.32', '0.66');

# 00000 = {result} ('http://empiremktxgjovhm.onion/product/117122/38/287986', datetime.datetime(2019, 11, 2, 4, 40,
# 44), 70.0, 'USD', 9243.33, 60.87, 58.48)
# 00001 = {result} ('http://empiremktxgjovhm.onion/product/106521/110/538217', datetime.datetime(2019, 10, 31, 8, 33,
#  5), 4.0, 'USD', 9100.34, 58.11, 58.61)
# 00002 = {result} ('http://empiremktxgjovhm.onion/product/33486/14/82637', datetime.datetime(2019, 10, 17, 4, 42,
# 40), 220.0, 'USD', 7968.6, 57.0, 52.57)
# 00003 = {result} ('/product/100712/102/204860', datetime.datetime(2019, 11, 11, 12, 10, 7), 10.26, 'USD', 8726.79,
# 61.58, 61.71)
# 00004 = {result} ('http://empiremktxgjovhm.onion/product/79824/73/189468', datetime.datetime(2019, 10, 23, 7, 3,
# 53), 0.01, 'USD', 7970.44, 56.54, 52.96)
# 00005 = {result} ('/product/54398/75/262450', datetime.datetime(2019, 11, 13, 7, 43, 49), 150.0, 'USD', 8740.77,
# 63.39, 61.35)
# 00006 = {result} ('http://empiremktxgjovhm.onion/product/31966/69/172860', datetime.datetime(2019, 10, 26, 10, 9,
# 53), 23.88, 'USD', 9207.85, 58.56, 56.09)
