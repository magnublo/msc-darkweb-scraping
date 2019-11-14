import re
import statistics
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import dateparser
from sqlalchemy.orm import Session

from src.db_utils import get_engine, get_db_session
from src.models.listing_observation import ListingObservation
from src.models.scraping_session import ScrapingSession


def load_dict(file_name: str) -> Dict[float, float]:
    with open(file_name, 'r') as file:
        lines = file.readlines()

    res = {}

    for line in lines[61:]:
        day_month, year, rate, _, _, _, _ = line.split(",")
        d = dateparser.parse(" ".join([day_month, year]))
        res[d.timestamp()] = float(rate)

    return res


def get_listing_observations(db_session: Session) -> List[tuple]:
    all_listing_observations = db_session.query(ListingObservation.id, ListingObservation.url,
                                                ListingObservation.created_date,
                                                ListingObservation.price, ListingObservation.fiat_currency,
                                                ListingObservation.btc_rate, ListingObservation.xmr_rate,
                                                ListingObservation.ltc_rate).join(ScrapingSession,
                                                                                  ScrapingSession.id ==
                                                                                  ListingObservation.session_id).filter(
        ScrapingSession.market == "EMPIRE_MARKET").all()
    return [l for l in all_listing_observations if l[5] is not None]


def get_listings_by_url(results: List[tuple]) -> Dict[str, List[tuple]]:
    url_dict = {}
    for id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate in results:
        if url not in url_dict.keys():
            url_dict[url] = [(id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate)]
        else:
            url_dict[url].append((id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate))

    return url_dict


def get_rate(x_per_usd_dict: Dict[float, float], date_time: datetime):
    t = date_time.timestamp()
    closest_timestamp = min(x_per_usd_dict.keys(), key=lambda k: abs(t - k))
    return x_per_usd_dict[closest_timestamp]


def get_currency_variances(listing_observations: List[Tuple]) -> Optional[Tuple]:
    arrs = btcs, xmrs, ltcs, usds, cads, auds, gbps, eurs = ([], [], [], [], [], [], [], [])
    # id, url, created_date, price, fiat_currency, btc_rate, xmr_rate, ltc_rate
    # cleaned_listing_observations = [l for l in listing_observations if l[5] is not None]
    for listing in listing_observations:
        _, url, date_time, usd_price, _, usd_per_btc, usd_per_xmr, usd_per_ltc = listing
        btcs.append(usd_price / usd_per_btc)
        xmrs.append(usd_price / usd_per_xmr)
        ltcs.append(usd_price / usd_per_ltc)
        cads.append(usd_price * get_rate(CAD_PER_USD_DICT, date_time))
        auds.append(usd_price * get_rate(AUD_PER_USD_DICT, date_time))
        gbps.append(usd_price * get_rate(GBP_PER_USD_DICT, date_time))
        eurs.append(usd_price * get_rate(EUR_PER_USD_DICT, date_time))
        usds.append(usd_price)

    return tuple([(n, statistics.variance(t)) for t, n in
                  zip(arrs, ('BTC', 'XMR', 'LTC', 'USD', 'CAD', 'AUD', 'GBP', 'EUR'))]) if len(btcs) > 1 else None


def get_line(url, underlying, min_var, second_min_var, btc_var, xmr_var, ltc_var, usd_var, cad_var, aud_var, gbp_var, eur_var) -> str:
    return f"({url}, {underlying}, {min_var-second_min_var}, {btc_var}, {xmr_var}, {ltc_var}, {usd_var}, {cad_var}, " \
           f"{aud_var}, {gbp_var}, {eur_var}), \n"


engine = get_engine()

DB_SESSION = get_db_session(engine)
CAD_PER_USD_DICT = load_dict('/home/magnus/PycharmProjects/msc/CAD_USD Historical Data.csv')
AUD_PER_USD_DICT = load_dict('/home/magnus/PycharmProjects/msc/AUD_USD Historical Data.csv')
GBP_PER_USD_DICT = load_dict('/home/magnus/PycharmProjects/msc/GBP_USD Historical Data.csv')
EUR_PER_USD_DICT = load_dict('/home/magnus/PycharmProjects/msc/EUR_USD Historical Data.csv')

assert CAD_PER_USD_DICT.keys() == AUD_PER_USD_DICT.keys() == GBP_PER_USD_DICT.keys() == EUR_PER_USD_DICT.keys()

lines = []
listings = get_listing_observations(DB_SESSION)
url_dict = get_listings_by_url(listings)

for i, url in zip(range(len(url_dict.keys())), url_dict.keys()):
    vars = get_currency_variances(url_dict[url])
    if vars is not None:
        btc_var, xmr_var, ltc_var, usd_var, cad_var, aud_var, gbp_var, eur_var = vars
        min_var, second_min_var = sorted(vars, key=lambda v: v[1])[0:2]
        lines.append(get_line(url, min_var[0], min_var[1], second_min_var[1], *vars))

    if i % 100:
        print(f"{i} of {len(listings)}")

with open('insert_variances_statement.txt', 'w') as f:
    f.writelines(lines)

DB_SESSION.close()

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
