import hashlib
import re
from datetime import datetime, timedelta, date
from typing import List, Tuple, Union, Callable, Any, Optional
from text2digits import text2digits

import dateparser
from bs4 import BeautifulSoup

from definitions import CRYPTONIA_WORLD_COUNTRY, CRYPTONIA_MARKET_EXTERNAL_MARKET_STRINGS, \
    DREAM_MARKET_ID, WALL_STREET_MARKET_ID, NUCLEUS_MARKET_ID, ALPHA_BAY_MARKET_ID, CGMC_MARKET_ID, HANSA_MARKET_ID, \
    BLACK_BANK_MARKET_ID, AGORA_MARKET_ID, BLACK_MARKET_RELOADED_ID, ABRAXAS_MARKET_ID, MIDDLE_EARTH_MARKET_ID, \
    FEEDBACK_TEXT_HASH_COLUMN_LENGTH, MD5_HASH_STRING_ENCODING, ONE_WEEK, EMPIRE_MARKET_ID
from src.base_functions import BaseFunctions
from src.db_utils import shorten_and_sanitize_for_text_column
from src.utils import _parse_float, _parse_int

ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS = 7


def _parse_percent_positive_rating(label_div: BeautifulSoup) -> float:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span = spans[0]
    return float(span.text[:-1])


def _parse_disputes(label_div: BeautifulSoup) -> Tuple[int, int]:
    good_spans = [good_span for good_span in label_div.findAll('span', attrs={'class': 'good'})]
    assert len(good_spans) == 1
    good_span = good_spans[0]

    inner_spans = [span for span in good_span.findAll('span')]
    assert len(inner_spans) == 1
    inner_span = inner_spans[0]

    disputes_won = int(inner_span.text)

    bad_spans = [bad_span for bad_span in label_div.findAll('span', attrs={'class': 'good'})]
    assert len(bad_spans) == 1
    bad_span = bad_spans[0]

    disputes_lost = int(bad_span.text)

    return disputes_won, disputes_lost


def _get_sales_rating_max_rating_from_external_rating(info_string: str) -> Tuple[
    int, Union[float, Any], Optional[Any], None, None, None, Optional[str]]:
    unparsed_nr_of_sales, rating_string = info_string.split(" deals")

    rating_and_max_rating = rating_string.split("/")
    if len(rating_and_max_rating) == 2:
        rating, max_rating = [_parse_float(r) for r in rating_and_max_rating]
    elif len(rating_and_max_rating) == 1:
        rating, max_rating = (_parse_float(rating_and_max_rating[0]), None)
    else:
        raise AssertionError("Unknown rating format in external market verification.")
    good_reviews, neutral_reviews, bad_reviews = (None, None, None)

    if not unparsed_nr_of_sales[-1] == "+":
        free_text = None
    else:
        free_text = "nr of sales is lower estimate"

    sales = _parse_int(unparsed_nr_of_sales)

    return sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text


def _get_good_neutral_bad_reviews_from_external_rating(info_string: str) -> Tuple[
    None, None, None, Any, Any, Any, None]:
    sales, rating, max_rating, free_text = (None, None, None, None)
    good_reviews, neutral_reviews, bad_reviews = [_parse_int(a) for a in info_string.split("/")]
    return sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text


def _get_external_rating_tuple(market_id: str, info_string: str) -> Tuple[str, int, float, float, int, int, int, str]:
    if market_id in [EMPIRE_MARKET_ID, DREAM_MARKET_ID, AGORA_MARKET_ID, WALL_STREET_MARKET_ID, NUCLEUS_MARKET_ID, ABRAXAS_MARKET_ID,
                     MIDDLE_EARTH_MARKET_ID, CGMC_MARKET_ID]:
        res = _get_sales_rating_max_rating_from_external_rating(info_string)
    elif market_id in [ALPHA_BAY_MARKET_ID, BLACK_BANK_MARKET_ID, BLACK_MARKET_RELOADED_ID]:
        res = _get_good_neutral_bad_reviews_from_external_rating(info_string)
    elif market_id in [HANSA_MARKET_ID]:
        try:
            res = _get_sales_rating_max_rating_from_external_rating(info_string)
        except ValueError:
            res = _get_good_neutral_bad_reviews_from_external_rating(info_string)
    else:
        res = (None, None, None, None, None, None, info_string)

    sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text = res
    return market_id, sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text


def _parse_external_market_verifications(label_div: BeautifulSoup) -> List[
    Tuple[str, int, float, float, int, int, int, str]]:
    external_market_verifications: List[Tuple[str, int, float, float, int, int, int, str]] = []

    spans = [span for span in label_div.findAll('span')]
    if len(spans) > 0:
        verified_spans = [span for span in label_div.findAll('span', attrs={'class': 'verified'})]
        remaining_external_market_ratings = list(CRYPTONIA_MARKET_EXTERNAL_MARKET_STRINGS)
        for verified_span in verified_spans:
            for market_id, market_string in remaining_external_market_ratings:
                if verified_span.text.find(market_string) != -1:
                    parts = verified_span.text.split(market_string)
                    external_rating_tuple = _get_external_rating_tuple(market_id, "".join(parts))
                    external_market_verifications.append(external_rating_tuple)
                    remaining_external_market_ratings.remove((market_id, market_string))
                    break

        if len(external_market_verifications) != len(verified_spans):
            raise AssertionError(f"Unknown external market {verified_spans}")

    return external_market_verifications


def _parse_amount_on_escrow(label_div: BeautifulSoup) -> Tuple[str, float, str, float]:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span = spans[0]

    crypto_amount_str, crypto_currency_str, fiat_amount_str, fiat_currency_str = span.text.split()

    return crypto_currency_str, float(crypto_amount_str), fiat_currency_str[:-1], float(fiat_amount_str[1:])


def _parse_ships_from(label_div: BeautifulSoup) -> str:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span = spans[0]

    return span.text.strip()


def _parse_ships_to(label_div: BeautifulSoup) -> List[str]:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span = spans[0]

    return [s.strip() for s in span.text.split(",")]


def _parse_jabber_id(label_div: BeautifulSoup) -> str:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span = spans[0]

    return span.text.strip()


def _parse_fe_enabled(label_div: BeautifulSoup) -> bool:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span_text = spans[0].text

    if span_text == "Yes":
        return True
    elif span_text == "No":
        return False
    else:
        raise AssertionError("Unknown value for 'FE Enabled' field in user profile")


def _parse_member_since(label_div: BeautifulSoup) -> datetime:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span_text = spans[0].text

    return dateparser.parse(span_text)


def _find_last_online_text_delimiter(span_text: str) -> str:
    candidate_delimiters = ("Within the last", "Whithin the last")
    for delimiter in candidate_delimiters:
        if span_text.find(delimiter) != -1:
            return delimiter
    raise AssertionError(f"Unknown delimiter in '{span_text}'")


def _parse_last_online(label_div: BeautifulSoup) -> date:
    spans = [span for span in label_div.findAll('span')]
    assert len(spans) == 1
    span_text = spans[0].text

    delimiter = _find_last_online_text_delimiter(span_text)

    time_ago_string = span_text.split(delimiter)[1].strip()
    unit_amount_and_unit_type = time_ago_string.split()

    if len(unit_amount_and_unit_type) == 2:
        unparsed_unit_amount, unit_type = unit_amount_and_unit_type
    elif len(unit_amount_and_unit_type) == 1:
        unparsed_unit_amount, unit_type = (1, unit_amount_and_unit_type[0])
    else:
        raise AssertionError(f"Could not parse time unit and time amount in {unit_amount_and_unit_type}")

    unit_amount = unparsed_unit_amount if type(unparsed_unit_amount) == int else int(
        text2digits.Text2Digits().convert_to_digits(str(unparsed_unit_amount)))

    if unit_type[:3] == "day":
        last_online = datetime.utcnow() - timedelta(days=int(unit_amount))
    elif unit_type[:4] == "week":
        last_online = datetime.utcnow() - timedelta(seconds=int(unit_amount) * ONE_WEEK)
    elif unit_type == "hours":
        last_online = datetime.utcnow() - timedelta(hours=int(unit_amount))
    else:
        raise AssertionError

    return date(year=last_online.year, month=last_online.month, day=last_online.day)


def _get_current_page_and_total_pages(td_gridftr: BeautifulSoup) -> Tuple[int, int]:
    spans = [span for span in td_gridftr.findAll('span')]
    assert len(spans) >= 1
    for span in spans:
        try:
            current_page, total_pages = span.text.split(" of ")
            return int(current_page), int(total_pages)
        except ValueError as e:
            pass

    # noinspection PyUnboundLocalVariable
    raise e


class CryptoniaScrapingFunctions(BaseFunctions):

    @staticmethod
    def get_meta_refresh_interval(soup_html: BeautifulSoup) -> Tuple[int, str]:
        metas = [meta for meta in soup_html.findAll('meta') if
                 "http-equiv" in meta.attrs.keys() and meta["http-equiv"] == "refresh"]
        assert len(metas) == 1
        meta_content = metas[0]["content"]
        wait_interval, redirect_url = meta_content.split(";")

        return int(wait_interval), redirect_url.strip()

    @staticmethod
    def get_captcha_image_url(soup_html: BeautifulSoup) -> str:
        imgs = [img for img in soup_html.select('.login_captcha')]
        assert len(imgs) == 1
        return imgs[0]["src"]

    @staticmethod
    def accepts_currencies(soup_html: BeautifulSoup) -> Tuple[bool, bool, bool]:
        product_details_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_details'})]
        assert len(product_details_divs) == 1
        product_details_div = product_details_divs[0]

        imgs = [img for img in product_details_div.findAll('img', attrs={'style': 'height: 18px; max-width: 200px'})]
        accepts_btc = False
        accepts_multisig_btc = False
        accepts_xmr = False

        for img in imgs:
            if img["src"] == "/image/btc_nm.png": accepts_btc = True
            if img["src"] == "/image/btc_ms_nm.png": accepts_multisig_btc = True
            if img["src"] == "/image/xmr_nm.png": accepts_xmr = True

        return accepts_btc, accepts_multisig_btc, accepts_xmr

    @staticmethod
    def get_title(soup_html) -> str:
        raise NotImplementedError('')

    @staticmethod
    def get_description(soup_html: BeautifulSoup) -> str:
        tab_view_1_divs = [div for div in soup_html.findAll('div', attrs={'id': 'tabview1'})]
        assert len(tab_view_1_divs) == 1
        tab_view_1_div = tab_view_1_divs[0]

        content_divs = [div for div in tab_view_1_div.findAll('div', attrs={'class': 'content_div'})]
        assert len(content_divs) >= 1
        content_div = content_divs[0]

        return shorten_and_sanitize_for_text_column(content_div.text)

    @staticmethod
    def get_product_page_urls(soup_html) -> List[str]:
        product_page_urls = []

        tables = [table for table in soup_html.findAll('table', attrs={'style': 'width: 100%'})]
        assert len(tables) == 1
        table = tables[0]

        trs = [tr for tr in table.findAll('tr')]
        assert len(trs) <= 27

        for tr in trs[1:-1]:
            thumb_td, spacer_td, product_td, price_td, vendor_td = [td for td in tr.findAll('td')]
            hrefs = [href for href in product_td.findAll('a', href=True)]
            assert len(hrefs) == 1
            href = hrefs[0]
            product_page_urls.append(href["href"])

        assert len(product_page_urls) == len(trs) - 2

        return product_page_urls

    @staticmethod
    def get_nr_sold_since_date(soup_html) -> int:
        raise NotImplementedError('')

    @staticmethod
    def get_fiat_currency_and_price(soup_html) -> Tuple[str, int]:
        raise NotImplementedError('')

    @staticmethod
    def get_origin_country_and_destinations(soup_html: BeautifulSoup) -> Tuple[str, List[str]]:
        product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data'})]
        assert len(product_data_divs) >= ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS
        product_data_divs = [div for div in product_data_divs if div.find('label').text == "Ships from:"]
        assert len(product_data_divs) <= 1
        if len(product_data_divs) == 0:
            return CRYPTONIA_WORLD_COUNTRY, [CRYPTONIA_WORLD_COUNTRY]
        else:
            product_data_div = product_data_divs[0]

        lbllist_divs = [div for div in product_data_div.findAll('div', attrs={'class': 'lbllist'})]
        assert len(lbllist_divs) == 1
        lbllist_div = lbllist_divs[0]
        origin_to_dest, *dests = lbllist_div.text.split(",")
        origin, dest = origin_to_dest.split("→")
        dests = [a_dest.strip() for a_dest in ([dest] + dests)]

        return origin.strip(), dests

    @staticmethod
    def get_cryptocurrency_rates(soup_html: BeautifulSoup) -> Tuple[float, float]:
        rate_divs = [div for div in soup_html.findAll('div', attrs={'class': 'rate_div'})]
        assert len(rate_divs) == 1
        rate_div = rate_divs[0]

        smtexts = [span for span in rate_div.findAll('span', attrs={'class': 'smtext'})]
        assert len(smtexts) == 1
        smtext = smtexts[0]

        rates_string = smtext.text
        rates = rates_string.split("=")

        btc_usd_rate = float(rates[2].split(" ")[1])
        btc_xmr_rate = float(rates[4].split(" ")[1])
        xmr_usd_rate = btc_usd_rate / btc_xmr_rate

        return btc_usd_rate, xmr_usd_rate

    def _format_logger_message(self, message: str) -> str:
        return message

    @staticmethod
    def get_category_lists_and_urls(soup_html: BeautifulSoup) -> Tuple[List[List], List[str]]:
        sidebar_inners = [div for div in soup_html.findAll('div', attrs={'class': 'sidebar_inner'})]
        assert len(sidebar_inners) == 2
        sidebar_inner = sidebar_inners[1]
        chksubcats_divs = [div for div in sidebar_inner.findAll('div', attrs={'class': 'chksubcats'})]
        category_name_spans = [span for span in sidebar_inner.findAll('span', attrs={'class', 'lgtext'})]
        assert len(chksubcats_divs) == len(category_name_spans) == 10

        category_lists = []
        urls = []

        for chksubcats_div, category_name_span in zip(chksubcats_divs, category_name_spans):
            main_category_name = category_name_span.text.strip()
            subcategory_hrefs = [href for href in chksubcats_div.findAll('a', href=True)]
            for subcategory_href in subcategory_hrefs:
                subcategory_href_inner_text_parts = subcategory_href.text.split(" ")
                assert len(subcategory_href_inner_text_parts) == 2
                subcategory_name = subcategory_href_inner_text_parts[0].strip()
                categories = [main_category_name, subcategory_name]
                subcategory_base_url = subcategory_href["href"]
                category_lists.append(categories)
                urls.append(subcategory_base_url)

        assert len(category_lists) == len(urls)
        return category_lists, urls

    @staticmethod
    def get_nr_of_result_pages_in_category(soup_html: BeautifulSoup) -> int:
        tds = [td for td in soup_html.findAll('td', attrs={'class', 'gridftr'})]
        assert len(tds) == 1
        td: BeautifulSoup = tds[0]
        spans = [span for span in td.findAll('span')]
        assert (len(spans) == 2 or len(spans) == 3)
        span: BeautifulSoup = spans[1]
        parts_of_span = span.text.split(" ")
        assert len(parts_of_span) == 3
        return int(parts_of_span[2])

    @staticmethod
    def get_titles_sellers_and_seller_urls(soup_html: BeautifulSoup) -> Tuple[List[str], List[str], List[str]]:
        titles = []
        sellers = []
        seller_urls = []

        tables = [table for table in soup_html.findAll('table', attrs={'style': 'width: 100%'})]
        assert len(tables) == 1
        table = tables[0]

        trs = [tr for tr in table.findAll('tr')]
        assert len(trs) <= 27

        for tr in trs[1:-1]:
            thumb_td, spacer_td, product_td, price_td, vendor_td = [td for td in tr.findAll('td')]
            hrefs = [href for href in vendor_td.findAll('a', href=True)]
            assert len(hrefs) == 1
            href = hrefs[0]
            seller_urls.append(href['href'])
            sellers.append(href.text)

            divs = [div for div in
                    product_td.findAll('div', attrs={'style': 'margin-bottom: 5px; width: 270px; overflow: hidden'})]
            assert len(divs) == 1
            name_div = divs[0]
            titles.append(name_div.text)

        return titles, sellers, seller_urls

    @staticmethod
    def get_fiat_currency_and_price_and_unit_type(soup_html: BeautifulSoup) -> Tuple[str, float, str]:
        product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data'})]
        assert len(product_data_divs) >= ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS
        product_data_divs = [div for div in product_data_divs if div.find('label').text == "Price:"]
        assert len(product_data_divs) == 1
        product_data_div = product_data_divs[0]

        lg_spans = [span for span in product_data_div.findAll('span', attrs={'class': 'lgtext', 'style': ''})]
        assert len(lg_spans) == 1
        lg_span = lg_spans[0]
        price, currency_slash_unit = lg_span.text.split(" ")
        currency, unit = currency_slash_unit.split("/")
        return currency, float(price), unit

    @staticmethod
    def supports_escrow(soup_html: BeautifulSoup) -> bool:
        product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data'})]
        assert len(product_data_divs) >= ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS
        product_data_divs = [div for div in product_data_divs if div.find('label').text == "FE or Escrow:"]
        assert len(product_data_divs) == 1
        product_data_div = product_data_divs[0]

        spans = [span for span in product_data_div.findAll(lambda tag: tag.name == 'span' and
                                                                       tag.get('class') == ['verified'])]

        spans_length = len(spans)
        assert spans_length <= 1
        if spans_length == 1:
            assert spans[0].text == "ESCROW"
        return spans_length == 1

    @staticmethod
    def get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(soup_html: BeautifulSoup) -> Tuple[int, str, int]:
        product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data'})]
        assert len(product_data_divs) >= ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS
        product_data_divs = [div for div in product_data_divs if div.find('label').text == "In stock:"]
        assert len(product_data_divs) == 1
        product_data_div = product_data_divs[0]

        quantity = None

        spans = [span for span in product_data_div.findAll('span')]
        if len(spans) == 1:
            minimum_order_unit_amount = 1
        elif len(spans) == 2:
            minimum_order_unit_amount = int(spans[1].text.split()[2])
        elif len(spans) == 3 and "class" in spans[2].attrs.keys() and "error" in spans[2].attrs["class"]:
            minimum_order_unit_amount = int(spans[1].text.split()[2])
            quantity = 0
        else:
            raise AssertionError("Unknown format for 'In stock' field.")
        span = spans[0]

        quantity_and_unit_type = span.text.split(" ")
        assert len(quantity_and_unit_type) == 2
        quantity = quantity_and_unit_type[0] if quantity is None else quantity
        unit_type = quantity_and_unit_type[1]

        return int(quantity), unit_type, minimum_order_unit_amount

    @staticmethod
    def get_listing_type(soup_html: BeautifulSoup) -> str:
        product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data'})]
        assert len(product_data_divs) >= ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS
        product_data_divs = [div for div in product_data_divs if div.find('label').text == "Listing Type:"]
        assert len(product_data_divs) == 1
        product_data_div = product_data_divs[0]

        spans = [span for span in product_data_div.findAll('span')]
        assert len(spans) == 1
        span = spans[0]

        return span.text

    @staticmethod
    def get_shipping_methods(soup_html) -> Tuple[
        List[str], List[Union[int, None]], List[str], List[float], List[Union[str, None]], List[bool]]:

        shipselects = [select for select in
                       soup_html.findAll('select', attrs={'class': 'shipselect', 'name': 'shipping_method'})]

        assert len(shipselects) == 1
        shipselect = shipselects[0]

        options = [option for option in shipselect.findAll('option')]
        assert len(options) >= 2

        descriptions, days, currencies, prices, unit_names, price_is_per_units = [], [], [], [], [], []

        for option in options[1:]:
            description = "(".join(option.text.split("(")[:-1])[:-1]
            price_and_currency = option.text.split("(")[-1].split(" ")
            price, currency = float(price_and_currency[0]), price_and_currency[1][:-1]
            shipping_days, shipping_unit_name, price_is_per_unit = None, None, False
            descriptions.append(description), days.append(shipping_days), currencies.append(currency),
            prices.append(price), unit_names.append(shipping_unit_name), price_is_per_units.append(price_is_per_unit)

        return descriptions, days, currencies, prices, unit_names, price_is_per_units

    @staticmethod
    def get_bulk_prices(soup_html: BeautifulSoup) -> Tuple[
        List[int], List[Union[int, None]], List[float], List[float], List[float]]:
        all_product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data'})]
        product_data_divs = [div for div in soup_html.findAll('div', attrs={'class': 'product_data',
                                                                            'style': 'margin-top: 0; padding-top: 0'})]
        assert len(product_data_divs) <= len(all_product_data_divs) - ASSUMED_MINIMUM_NUMBER_OF_PRODUCT_DATA_DIVS

        bulk_lower_bounds, bulk_upper_bounds, bulk_fiat_prices, bulk_btc_prices, bulk_discount_percents = [], [], [], \
                                                                                                          [], []

        for product_data_div in product_data_divs:
            labels = [label for label in product_data_div.findAll('label')]
            assert len(labels) == 1
            label = labels[0]
            bulk_lower_bound = int(label.text.split(" ")[0])

            spans = [span for span in product_data_div.findAll('span')]
            assert len(spans) == 3
            assert spans[1].attrs == {}
            assert spans[2].attrs["class"] == ["pricetag"]

            lg_text = spans[0]
            bulk_fiat_price = float(lg_text.text.split("/")[0].split(" ")[0])

            no_class_span = spans[1]
            bulk_btc_price = float(no_class_span.text.split("/")[0].split(" ")[0][1:])

            pricetag_span = spans[2]
            discount_percent = pricetag_span.text.split("%")[0]

            bulk_lower_bounds.append(bulk_lower_bound)
            bulk_fiat_prices.append(bulk_fiat_price)
            bulk_btc_prices.append(bulk_btc_price)
            bulk_discount_percents.append(discount_percent)

        for i in range(len(bulk_lower_bounds) - 1):
            bulk_upper_bounds.append(bulk_lower_bounds[i + 1] - 1)

        assert max(len(bulk_lower_bounds), 1) - 1 == len(bulk_upper_bounds)

        for i in range(len(bulk_lower_bounds) - len(bulk_upper_bounds)):
            bulk_upper_bounds.append(None)

        return bulk_lower_bounds, bulk_upper_bounds, bulk_fiat_prices, bulk_btc_prices, bulk_discount_percents

    @staticmethod
    def get_seller_about_description(soup_html: BeautifulSoup) -> str:
        target_content_divs = [div for div in
                               soup_html.findAll('div', attrs={'id': 'general_div', 'class': 'target_content'})]
        assert len(target_content_divs) == 1
        target_content_div = target_content_divs[0]

        return shorten_and_sanitize_for_text_column(target_content_div.text)

    @staticmethod
    def get_seller_info(soup_html: BeautifulSoup) -> Tuple[
        float, Tuple[int, int], List[Tuple[str, int, float, float, int, int, int, str]], Tuple[
            str, float, str, float], str, List[str], any, bool, datetime, date]:

        res = []

        expected_labels_and_parsing_funcs = [[_parse_percent_positive_rating, "Positive:"],
                                             [_parse_disputes, "Disputes (won/lost):"],
                                             [_parse_external_market_verifications, "Verifications:"],
                                             [_parse_amount_on_escrow, "Amount on Escrow:"],
                                             [_parse_ships_from, "Ships From:"],
                                             [_parse_ships_to, "Ships To:"],
                                             [_parse_jabber_id, "XMPP/Jabber ID:"],
                                             [_parse_fe_enabled, "FE Enabled:"],
                                             [_parse_member_since, "Member since:"],
                                             [_parse_last_online, "Last online:"]]

        inline_divs = [inline_div for inline_div in soup_html.findAll('div', attrs={'class': 'inline_div'})]
        assert len(inline_divs) <= 2
        seller_info_div = inline_divs[-1]

        label_divs = [label_div for label_div in seller_info_div.findAll('div') if
                      'class' not in label_div.attrs.keys()]
        assert len(label_divs) <= len(expected_labels_and_parsing_funcs)

        for i, label_div in zip(range(len(label_divs)), label_divs):
            k = 0
            expected_label = expected_labels_and_parsing_funcs[k][1]
            labels = [label for label in label_div.findAll('label')]
            if 'lbllist' in [item for sublist in label_div.attrs.values() for item in sublist]:
                assert len(labels) == 0
            else:
                assert len(labels) == 1
            label = labels[0]
            while label.text != expected_label:
                res.append([])
                k += 1
                expected_label = expected_labels_and_parsing_funcs[k][1]
            func: Callable[[str], any] = expected_labels_and_parsing_funcs[k][0]
            res.append(func(label_div))
            expected_labels_and_parsing_funcs = expected_labels_and_parsing_funcs[k + 1:]
            k += 1

        percent_positive_rating: float = res[0]
        disputes: Tuple[int, int] = res[1]
        external_market_verifications: List[Tuple[str, int, float, float, int, int, int, str]] = res[2]
        amount_on_escrow: Tuple[str, float, str, float] = res[3]
        ships_from: str = res[4]
        ships_to: List[str] = res[5]
        jabber_id: str = res[6]
        fe_enabled: bool = res[7]
        member_since: datetime = res[8]
        last_online: date = res[9]

        if not jabber_id:
            jabber_id = None
        if not ships_from:
            ships_from = None

        return percent_positive_rating, disputes, external_market_verifications, amount_on_escrow, ships_from, \
               ships_to, \
               jabber_id, fe_enabled, member_since, last_online

    @staticmethod
    def get_parenthesis_number_and_vendor_level(soup_html: BeautifulSoup) -> Tuple[int, int]:
        h2s = [h2 for h2 in soup_html.findAll('h2')]
        assert len(h2s) >= 1
        h2 = h2s[0]

        parenthesis_string, level_string = [s.strip() for s in h2.text.split("\n")]
        parenthesis_number = int(parenthesis_string.split("\xa0")[1][1:-1])
        level_number = int(level_string.split()[1])

        return parenthesis_number, level_number

    @staticmethod
    def get_feedbacks(soup_html: BeautifulSoup) -> Tuple[
        Tuple[date], Tuple[str], Tuple[str], Tuple[str], Tuple[str], Tuple[str], Tuple[str], Tuple[float]]:
        target_content_divs = [div for div in
                               soup_html.findAll('div', attrs={'id': 'feedback_div', 'class': 'target_content'})]
        assert len(target_content_divs) == 1
        target_content_div = target_content_divs[0]

        is_last_page = CryptoniaScrapingFunctions.get_next_feedback_url(soup_html) is None

        table_rows = [tr for tr in target_content_div.findAll('tr')]

        if is_last_page:
            assert len(table_rows) <= 27
        else:
            assert len(table_rows) == 27

        publication_dates: List[date] = []
        feedback_categories: List[str] = []
        titles: List[str] = []
        feedback_message_texts: List[str] = []
        text_hashes: List[str] = []
        buyers: List[str] = []
        crypto_currencies: List[str] = []
        prices: List[float] = []

        for row in table_rows[1:-1]:
            spans = [span for span in row.findAll('span')]
            assert len(spans) == 5

            paragraphs = [p for p in row.findAll('p')]
            assert len(paragraphs) == 1

            feedback_category_span = spans[0]

            tag_attributes = [item for sublist in feedback_category_span.attrs.values() for item in sublist]
            if 'icono-checkCircle' in tag_attributes and len(tag_attributes) == 13:
                feedback_category = "Positive Feedback"
            elif 'icono-crossCircle' in tag_attributes and len(tag_attributes) == 11:
                feedback_category = "Negative Feedback"
            else:
                raise AssertionError(f"Unknown feedback type {tag_attributes}")

            product_title_span = spans[1]
            title = product_title_span.text

            feedback_message_paragraph = paragraphs[0]
            feedback_text = feedback_message_paragraph.text

            date_span = spans[2]
            year, month, day = [int(s) for s in date_span.text.split("-")]
            publication_date = date(year=year, month=month, day=day)

            price_span = spans[3]
            price_and_cryptocurrency = price_span.text.split()
            assert len(price_and_cryptocurrency) == 2
            price = float(price_and_cryptocurrency[0])
            crypto_currency = price_and_cryptocurrency[1]
            assert len(crypto_currency) == 3

            buyer_username_span = spans[4]
            buyer = buyer_username_span.text

            publication_dates.append(publication_date)
            feedback_categories.append(feedback_category)
            titles.append(title)
            feedback_message_texts.append(feedback_text)
            text_hashes.append(hashlib.md5(
                feedback_text.encode(MD5_HASH_STRING_ENCODING)
            ).hexdigest()[:FEEDBACK_TEXT_HASH_COLUMN_LENGTH])
            buyers.append(buyer)
            crypto_currencies.append(crypto_currency)
            prices.append(price)

        return tuple(publication_dates), tuple(feedback_categories), tuple(titles), tuple(
            feedback_message_texts), tuple(text_hashes), tuple(buyers), tuple(crypto_currencies), tuple(prices)

    @staticmethod
    def get_next_feedback_url(soup_html: BeautifulSoup) -> Union[str, None]:
        td_gridftrs = [td for td in soup_html.findAll('td', attrs={'class': 'gridftr', 'colspan': '5'})]
        if len(td_gridftrs) == 0:
            return None
        elif len(td_gridftrs) == 1:
            td_gridftr = td_gridftrs[0]
            current_page, total_pages = _get_current_page_and_total_pages(td_gridftr)

            a_tags = [a_tag for a_tag in td_gridftr.findAll('a', href=True)]

            if current_page == total_pages and len(a_tags) == 0:
                return None
            elif current_page == total_pages and len(a_tags) == 1:
                return None
            elif current_page == total_pages and len(a_tags) == 2:
                raise AssertionError
            elif current_page != total_pages and len(a_tags) == 1:
                return a_tags[0]["href"]
                # return the first
            elif current_page != total_pages and len(a_tags) == 2:
                return a_tags[1]["href"]
                # return last of the two
        else:
            raise AssertionError("Unrecognized feedback tab pagination.")

    @staticmethod
    def get_pgp_key(soup_html: BeautifulSoup) -> Union[str, None]:
        target_content_divs = [div for div in
                               soup_html.findAll('div', attrs={'id': 'pgp_div', 'class': 'target_content'})]
        assert len(target_content_divs) == 1
        target_content_div = target_content_divs[0]

        text_areas = [text_area for text_area in
                      target_content_div.findAll('textarea', attrs={'class': 'ascii_armour_textarea'})]
        if len(text_areas) == 0:
            return None
        elif len(text_areas) == 1:
            text_area = text_areas[0]
            return shorten_and_sanitize_for_text_column(text_area.text)
        else:
            raise AssertionError("Unknown page formatting when scraping PGP key")

    @staticmethod
    def get_terms_and_conditions(soup_html: BeautifulSoup) -> Union[str, None]:
        target_content_divs = [div for div in
                               soup_html.findAll('div', attrs={'id': 'terms_div', 'class': 'target_content'})]
        assert len(target_content_divs) == 1
        target_content_div = target_content_divs[0]

        content_divs = [content_div for content_div in
                        target_content_div.findAll('div', attrs={'class': 'content_div'})]
        if len(content_divs) == 0:
            return None
        elif len(content_divs) == 1:
            content_div = content_divs[0]
            return shorten_and_sanitize_for_text_column(content_div.text)
        else:
            raise AssertionError("Unknown page formatting when scraping terms and conditions")

    @staticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:
        payload = {}

        inputs = [input for input in soup_html.findAll('input')]
        assert len(inputs) == 5
        username_input = inputs[0]
        assert username_input["type"] == "input"
        password_input = inputs[1]
        assert password_input["type"] == "password"
        captcha_input = inputs[2]
        assert captcha_input["type"] == "text"
        hidden_input = inputs[3]
        assert hidden_input["type"] == "hidden"
        submit_input = inputs[4]
        assert submit_input["type"] == "submit"

        sess_code = hidden_input["value"]
        submit_value = submit_input["value"]

        payload[username_input["name"]] = username
        payload[password_input["name"]] = password
        payload[captcha_input["name"]] = captcha_solution
        payload[hidden_input["name"]] = sess_code
        payload[submit_input["name"]] = submit_value

        return payload
