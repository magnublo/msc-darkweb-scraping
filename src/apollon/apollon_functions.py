import datetime
import hashlib
import re
from math import ceil
from typing import Tuple, Set, List, Optional

import dateparser
from bs4 import BeautifulSoup

from definitions import APOLLON_MARKET_CATEGORY_INDEX_URL_PATH, APOLLON_MARKET_EXTERNAL_MARKET_STRINGS, \
    MD5_HASH_STRING_ENCODING, FEEDBACK_TEXT_HASH_COLUMN_LENGTH
from src.base.base_functions import BaseFunctions
from src.db_utils import shorten_and_sanitize_for_text_column
from src.utils import parse_int, ListingType, parse_float
from src.base.base_functions import BaseFunctions, get_external_rating_tuple


class ApollonScrapingFunctions(BaseFunctions):

    @staticmethod
    def is_logged_in(soup_html: BeautifulSoup, username: str) -> bool:
        username_in_dropdown = soup_html.select_one(
            "#wrapper > nav > div > ul.nav.navbar-nav.navbar-right > li.dropdown > ul > li:nth-child(1) > a > big")
        return username_in_dropdown and username_in_dropdown.text == username

    @staticmethod
    def get_captcha_image_url_from_market_page(soup_html: BeautifulSoup) -> str:
        img_tags = soup_html.select(
            "#page-wrapper > div > div > div > div.panel-body > form > fieldset > div:nth-child(4) > img")

        assert len(img_tags) == 1
        img_tag = img_tags[0]

        return f"/{img_tag['src']}"

    @staticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:
        inputs = soup_html.select(
            "#page-wrapper > div > div > div > div.panel-body > form > fieldset > div > input")

        assert len(inputs) == 3

        return {
            inputs[0]["name"]: username,
            inputs[1]["name"]: password,
            inputs[2]["name"]: captcha_solution
        }

    @staticmethod
    def get_meta_refresh_interval(soup_html: BeautifulSoup) -> Tuple[int, str]:
        raise NotImplementedError('')

    @staticmethod
    def get_captcha_instruction(soup_html: BeautifulSoup) -> str:
        captcha_code_input = soup_html.select_one(
            "#page-wrapper > div > div > div > div.panel-body > form > fieldset > div:nth-child(3) > input")

        return captcha_code_input["placeholder"]

    @staticmethod
    def get_sub_categories_index_urls(soup_html: BeautifulSoup) -> Tuple[Tuple[str], Tuple[str]]:
        # This function shall return
        # (1) main category URLs which only have one level of children
        # (2) subcategory URLs which only have one level of children
        # both of which, should, constitute the set of all categories.
        HOME = APOLLON_MARKET_CATEGORY_INDEX_URL_PATH

        category_search_select: BeautifulSoup = soup_html.select_one(
            "#wrapper > div.navbar-default.sidebar > div:nth-child(2) > div.panel-body > form > fieldset > div > div "
            "> select:nth-child(9)")

        assert category_search_select["name"] == 'ss_subcat'

        category_id_tuples = [o.attrs["value"] for o in category_search_select.select("option") if "value" in o.attrs]
        category_name_tuples = [o.text for o in category_search_select.select("option") if "value" in o.attrs]

        parent_sub_categories_index_urls: Set[str] = set()
        main_categories_index_urls: Set[str] = set()

        # example url: http://apollon2tclejj73.onion/home.php?cid=1&csid=1
        for category_id_tuple, category_name_tuple_str in zip(category_id_tuples, category_name_tuples):
            category_name_tuple = [s.strip() for s in category_name_tuple_str.split("=>")]
            c_id, sc_id, ssc_id = [int(s) for s in category_id_tuple.split("|")]
            if len(category_name_tuple) == 2:
                # category with one level of children
                main_categories_index_urls.add(f"{HOME}?cid={c_id}")
            elif len(category_name_tuple) == 3:
                # category with two levels of children
                parent_sub_categories_index_urls.add(f"{HOME}?cid={c_id}&csid={sc_id}")
            else:
                raise AssertionError("Encountered category with neither one nor two levels of children.")

        return tuple(main_categories_index_urls), tuple(parent_sub_categories_index_urls)

    @staticmethod
    def get_task_list_from_parent_sub_category_page(soup_html: BeautifulSoup) -> Tuple[Tuple[Tuple, str]]:
        tasks: List[Tuple[Tuple, str]] = []

        sub_sub_categories_urls_and_nrs_of_listings = \
            ApollonScrapingFunctions.get_sub_sub_categories_urls_and_nrs_of_listings(
                soup_html)
        for sub_sub_category, sub_sub_category_url, nr_of_listings in sub_sub_categories_urls_and_nrs_of_listings:
            nr_of_pages = ceil(nr_of_listings / 15)
            for k in range(0, nr_of_pages):
                page_url_in_category = f"{sub_sub_category_url}&ss_home=2&pg={k + 1}"
                tasks.append(
                    (sub_sub_category, page_url_in_category))

        return tuple(tasks)

    @staticmethod
    def get_task_list_from_main_category_page(soup_html: BeautifulSoup) -> Tuple[Tuple[None, str]]:
        tasks: List[Tuple[None, str]] = []

        parent_sub_categories_urls_and_nrs_of_listings = \
            ApollonScrapingFunctions.get_parent_sub_category_urls_and_nrs_of_listings(
                soup_html)

        for category, parent_sub_category_url, nr_of_listings in parent_sub_categories_urls_and_nrs_of_listings:
            nr_of_pages = ceil(nr_of_listings / 15)
            for k in range(0, nr_of_pages):
                page_url_in_category = f"{parent_sub_category_url}&ss_home=2&pg={k + 1}"
                tasks.append((category, page_url_in_category))

        return tuple(tasks)

    @staticmethod
    def get_sub_sub_categories_urls_and_nrs_of_listings(soup_html: BeautifulSoup) -> Tuple[Tuple[Tuple, str, int]]:
        sub_sub_category_hrefs = soup_html.select(
            "#wrapper > div.navbar-default.sidebar > div:nth-child(1) > ul > ul > li > ul > li > a")
        sub_sub_categories_urls_and_nrs_of_listings: List[Tuple[Tuple, str, int]] = []
        a: BeautifulSoup
        for a in sub_sub_category_hrefs:
            stripped_text = a.text.strip()
            match = re.match(r"^(.+)\s+\[(\s+[0-9]+\s+)\]$", stripped_text)
            assert match
            category_name = stripped_text[match.regs[1][0]:match.regs[1][1]].strip()
            parent_category_name = ApollonScrapingFunctions.get_currently_selected_parent_sub_category(soup_html)
            category = (category_name, None, parent_category_name, 2)
            nr_of_listings = parse_int(stripped_text[match.regs[2][0]:match.regs[2][1]].strip())
            sub_sub_categories_urls_and_nrs_of_listings.append((category, f"/{a['href']}", nr_of_listings))

        return tuple(sub_sub_categories_urls_and_nrs_of_listings)

    @staticmethod
    def get_parent_sub_category_urls_and_nrs_of_listings(soup_html: BeautifulSoup) -> Tuple[Tuple[None, str, int]]:
        HOME = APOLLON_MARKET_CATEGORY_INDEX_URL_PATH
        parent_sub_category_hrefs = soup_html.select("#side-menu > ul > li > a")
        # #side-menu > ul:nth-child(4) > li > a
        parent_sub_categories_urls_and_nrs_of_listings: List[Tuple[None, str, int]] = []

        a: BeautifulSoup
        for a in parent_sub_category_hrefs:
            stripped_text = a.text.strip()
            match = re.match(r"^(.+)\s+\[(\s+[0-9]+\s+)\]$", stripped_text)
            assert match
            nr_of_listings = parse_int(stripped_text[match.regs[2][0]:match.regs[2][1]].strip())
            parent_sub_categories_urls_and_nrs_of_listings.append((None, f"{HOME}{a['href']}", nr_of_listings))

        return tuple(parent_sub_categories_urls_and_nrs_of_listings)

    @staticmethod
    def get_currently_selected_main_category(soup_html: BeautifulSoup) -> str:
        side_menu: BeautifulSoup = soup_html.select_one("#side-menu")
        children = [c for c in side_menu.children]
        for i, child in enumerate(children[:-1]):
            child: BeautifulSoup
            next_child = children[i + 1]
            if child.name == "li" and next_child.name != "li":
                stripped_text = child.text.strip()
                match = re.match(r"^(.+)\s+\[(\s+[0-9]+\s+)\]$", stripped_text)
                assert match
                return stripped_text[match.regs[1][0]:match.regs[1][1]].strip()

        raise AssertionError("Could not determine which main category is selected in sidebar.")

    @staticmethod
    def get_currently_selected_parent_sub_category(soup_html: BeautifulSoup) -> str:
        all_sub_categories = soup_html.select("#side-menu > ul")
        for sub_category in all_sub_categories:
            sub_category: BeautifulSoup
            sub_li = sub_category.select_one("li")
            sub_uls = sub_li.select("ul")
            if len(sub_uls) > 0:
                stripped_text = sub_category.text.strip().split("\n", maxsplit=1)[0].strip()
                match = re.match(r"^(.+)\s+\[(\s+[0-9]+\s+)\]$", stripped_text)
                assert match
                return stripped_text[match.regs[1][0]:match.regs[1][1]].strip()

        raise AssertionError("Could not determine which parent sub category is selected in sidebar.")

    @staticmethod
    def get_listing_infos(soup_html: BeautifulSoup):
        # product_page_urls, titles, urls_is_sticky, sellers, seller_urls, nrs_of_views, publication_dates, categories
        product_divs = soup_html.select("#page-wrapper > div > div > div > table > tbody > tr > td > div")
        product_urls = []
        titles = []
        urls_is_sticky = []
        sellers = []
        seller_urls = []
        nrs_of_views = []
        publication_dates = []
        categories = []

        div: BeautifulSoup
        for div in product_divs:
            product_a_tag = div.select_one("div.col-sm-8 > small:nth-child(1) > a")
            product_url = '/' + product_a_tag["href"]
            product_title = product_a_tag.text.strip()
            is_sticky_b = div.select_one("div.col-sm-8 > small:nth-child(1) > b")
            is_sticky = is_sticky_b.text.strip() == "[Sticky]" if is_sticky_b else False
            _, created_date_str, category_str, _ = div.select_one("div.col-sm-8 > small:nth-child(3)").text.split("-|-")
            created_date = dateparser.parse("".join(created_date_str.split()[1:]))
            main_category_name, sub_category_name = [s.strip() for s in category_str.split("/")]
            category_pair = ((main_category_name, None, None, 0), (sub_category_name, None, main_category_name, 1))
            seller_a_tag = div.select_one("div.col-sm-8 > small:nth-child(3) > a:nth-child(4)")
            seller_url = '/' + seller_a_tag["href"]
            seller = seller_a_tag.text.strip()
            t = div.text
            match = re.search(r"Sold\s:\s[0-9]+\s\/\sViews\s:\s([0-9]+)", div.text)
            nr_of_views = parse_int(div.text[match.regs[1][0]:match.regs[1][1]])
            product_urls.append(product_url)
            urls_is_sticky.append(is_sticky)
            titles.append(product_title)
            sellers.append(seller)
            seller_urls.append(seller_url)
            nrs_of_views.append(nr_of_views)
            publication_dates.append(created_date)
            categories.append(category_pair)

        return tuple(product_urls), tuple(titles), tuple(urls_is_sticky), tuple(sellers), tuple(seller_urls), tuple(
            nrs_of_views), tuple(publication_dates), tuple(categories)

    @staticmethod
    def get_cryptocurrency_rates(soup_html: BeautifulSoup) -> Tuple[float, float, float, float]:
        # #wrapper > div.navbar-default.sidebar > div.navbar-default.sidebar > div:nth-child(2)
        usd_rates = [float(f.text) for f in soup_html.select(
            "#wrapper > div.navbar-default.sidebar > div.navbar-default.sidebar > div:nth-child(2) > div > div > div "
            "> span:nth-child(2)")]
        assert len(usd_rates) == 4
        # noinspection PyTypeChecker
        return tuple(usd_rates)

    @staticmethod
    def accepts_currencies(soup_html: BeautifulSoup) -> Tuple[bool, bool, bool]:
        buttons = soup_html.select(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > form > div > div > button")
        accepts_XMR, accepts_BCH, accepts_LTC = (False, False, False)
        for b in buttons[1:]:
            curr = b.text.strip().split()[-1]
            if curr == "XMR":
                accepts_XMR = True
                continue
            elif curr == "BCH":
                accepts_BCH = True
                continue
            elif curr == "LTC":
                accepts_LTC = True
                continue
            else:
                raise AssertionError(f"Unknown currency '{curr}'.")

        return accepts_XMR, accepts_BCH, accepts_LTC

    @staticmethod
    def get_sales(soup_html: BeautifulSoup) -> int:
        sales_i = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > div:nth-child(3) > small:nth-child(1) > span > i")
        assert sales_i is not None
        return int(sales_i.text)

    @staticmethod
    def get_fiat_price(soup_html: BeautifulSoup) -> Optional[float]:
        price_span = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > form > div > h5:nth-child(1) > span")
        if price_span:
            return float(price_span.text.split("/")[0].split(":")[-1].strip().split()[0])
        else:
            return None

    @staticmethod
    def get_origin_country(soup_html: BeautifulSoup) -> str:
        origin_country_span = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > div:nth-child(3) > small:nth-child(3)")
        assert origin_country_span is not None
        return origin_country_span.text.split(":")[-1].strip()

    @staticmethod
    def get_destination_countries(soup_html: BeautifulSoup) -> Tuple[str]:
        listing_div = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > div:nth-child(3)")
        listing_div_text = listing_div.text
        start_index = listing_div_text.find("Ship to : ") + len("Ship to : ")
        end_index = listing_div_text.find("Payment :")
        dests_string = listing_div_text[start_index:end_index].strip()
        destination_countries: List[str] = [dests_string[a.regs[0][0]:a.regs[0][1]].strip() for a in
                                            BaseFunctions.COMMA_SEPARATED_COUNTRY_REGEX.finditer(dests_string)]
        return tuple(destination_countries)

    @staticmethod
    def get_payment_method(soup_html: BeautifulSoup) -> Tuple[bool, bool]:
        # return boolean tuple escrow, fifty_percent_finalize_early
        listing_div = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > div:nth-child(3)")
        listing_div_text = listing_div.text
        start_index = listing_div_text.find("Payment : ") + len("Payment : ")
        end_index = listing_div_text.find("Product class :")
        payment_type_str = listing_div_text[start_index:end_index].strip()

        supports_escrow = False
        supports_fifty_percent_finalize_early = False

        if payment_type_str == "Full Escrow":
            supports_escrow = True
        elif payment_type_str == "Finalize Early":
            pass
        elif payment_type_str == "50% Finalize Early":
            supports_fifty_percent_finalize_early = True
        else:
            raise AssertionError("Unknown payment type.")

        return supports_escrow, supports_fifty_percent_finalize_early

    @staticmethod
    def get_standardized_listing_type(soup_html: BeautifulSoup) -> ListingType:
        listing_div = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > div:nth-child(3)")
        listing_div_text = listing_div.text
        start_index = listing_div_text.find("Product class : ") + len("Product class : ")
        end_index = listing_div_text.find("Quantity :")
        product_class_str = listing_div_text[start_index:end_index].strip()

        if product_class_str == "Physical Package":
            listing_type = ListingType.PHYSICAL
        elif product_class_str == "Digital Goods":
            listing_type = ListingType.MANUAL_DIGITAL
        else:
            raise AssertionError(f"Unknown product class {product_class_str}.")
        return listing_type

    @staticmethod
    def get_quantity_in_stock(soup_html: BeautifulSoup) -> Optional[int]:
        listing_div = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > div:nth-child(3)")
        listing_div_text = listing_div.text
        start_index = listing_div_text.find("Quantity : ") + len("Quantity : ")
        quantity_str = listing_div_text[start_index:].strip()
        if quantity_str == "This item is out of stock !!!":
            quantity_in_stock = 0
        elif quantity_str == "Unlimited Available":
            quantity_in_stock = None
        else:
            quantity_in_stock = parse_int(quantity_str)
        return quantity_in_stock

    @staticmethod
    def get_shipping_methods(soup_html: BeautifulSoup) -> Tuple[Tuple[Optional[str], int, str, float, Optional[str], bool]]:
        # description, days_shipping_time, fiat_currency, price, quantity_unit_name, price_is_per_unit
        shipping_methods: List[Tuple[Optional[str], int, str, float, Optional[str], bool]] = []
        option_texts = [s.text.strip() for s in soup_html.select(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(1) > td > "
            "div:nth-child(2) > form > div > div.form-group.form-inline > select > option")]
        for o in option_texts:
            description_str, time_str, price_str = [s.strip() for s in f" {o} ".rsplit(" - ", maxsplit=2)]
            description = description_str if description_str else None
            nr_of_days_str, day_str = [s for s in time_str.strip().split()]
            assert day_str[0:3] == "Day"
            days = parse_int(nr_of_days_str)
            fiat_price_str, crypto_price_str = [s.strip() for s in price_str.strip().split("/")]
            fiat_price_str, fiat_currency = [s for s in fiat_price_str.split()]
            fiat_price = parse_float(fiat_price_str)
            quantity_unit_name, price_is_per_unit = (None, False)
            shipping_methods.append(
                (description, days, fiat_currency, fiat_price, quantity_unit_name, price_is_per_unit))

        return tuple(shipping_methods)

    @staticmethod
    def get_listing_text(soup_html: BeautifulSoup) -> str:
        listing_text_pre = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div > div > div > table > tbody > tr:nth-child(2) > td > div "
            "> div > div > div > div > pre")
        assert listing_text_pre is not None
        return shorten_and_sanitize_for_text_column(listing_text_pre.text)

    @staticmethod
    def get_seller_about_description(soup_html: BeautifulSoup) -> str:
        description_div = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div.tab-content > div > div > div > div > div.col-sm-8")
        assert description_div is not None
        return shorten_and_sanitize_for_text_column(description_div.text)

    @staticmethod
    def get_email_and_jabber_id(soup_html: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        jabber_span, email_span = soup_html.select(
            "#page-wrapper > div > div.col-lg-12.left > div.tab-content > div > div > div > div > div.col-sm-5 > span")
        jabber_id = jabber_span.text.split(":")[-1].strip()
        email = email_span.text.split(":")[-1].strip()

        email = email if email else None
        jabber_id = jabber_id if jabber_id else None

        return email, jabber_id

    @staticmethod
    def get_seller_and_trust_level(soup_html: BeautifulSoup) -> Tuple[int, int]:
        level_smalls = soup_html.select(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-5 > "
            "small:nth-child(1) > small")
        assert len(level_smalls) == 2
        seller_level = int(level_smalls[0].text.strip().split()[2])
        trust_level = int(level_smalls[1].text.strip().split()[2])
        return seller_level, trust_level

    @staticmethod
    def get_positive_feedback_percent(soup_html: BeautifulSoup) -> float:
        username_b = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-5 > "
            "small:nth-child(1) > a > b")
        assert username_b is not None
        return parse_float(username_b.text.strip().split()[
                               -1][1:-2])

    @staticmethod
    def get_registration_date(soup_html: BeautifulSoup):
        left_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-5")
        assert left_card is not None
        left_card_text = left_card.text
        match = re.search(r"Member\ssince\s:\s([A-Z][a-z]{2}\s[0-9]{2},\s[0-9]{4})", left_card_text)
        date_str = left_card_text[match.regs[1][0]:match.regs[1][1]]
        registration_date = dateparser.parse(date_str)
        return registration_date

    @staticmethod
    def get_last_login(soup_html: BeautifulSoup):
        left_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-5")
        assert left_card is not None
        left_card_text = left_card.text
        match = re.search(r"Last\sLogin\s:\s([A-Z][a-z]{2}\s[0-9]{2},\s[0-9]{4})", left_card_text)
        date_str = left_card_text[match.regs[1][0]:match.regs[1][1]]
        last_login = dateparser.parse(date_str)
        return last_login

    @staticmethod
    def get_sales_by_seller(soup_html: BeautifulSoup) -> int:

        right_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-2")
        assert right_card is not None
        right_card_text = right_card.text
        match = re.search(r"Sales\s:\s([^A-z]+)", right_card_text)
        sales_str = right_card_text[match.regs[1][0]:match.regs[1][1]]
        nr_of_sales = parse_int(sales_str)
        return nr_of_sales

    @staticmethod
    def get_orders(soup_html: BeautifulSoup) -> int:

        right_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-2")
        assert right_card is not None
        right_card_text = right_card.text
        match = re.search(r"Orders\s:\s([^A-z]+)", right_card_text)
        orders_str = right_card_text[match.regs[1][0]:match.regs[1][1]]
        nr_of_orders = parse_int(orders_str)
        return nr_of_orders

    @staticmethod
    def get_disputes(soup_html: BeautifulSoup) -> Tuple[int, int]:

        right_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-2")
        assert right_card is not None
        right_card_text = right_card.text
        match = re.search(r"Won\/Lost\sDisputes\s:\s([0-9]+)\/([0-9]+)", right_card_text)
        disputes_won_str = right_card_text[match.regs[1][0]:match.regs[1][1]]
        disputes_lost_str = right_card_text[match.regs[2][0]:match.regs[2][1]]
        won, lost = (parse_int(disputes_won_str), parse_int(disputes_lost_str))
        return won, lost

    @staticmethod
    def get_fe_allowed(soup_html: BeautifulSoup) -> bool:

        right_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-2")
        assert right_card is not None
        right_card_text = right_card.text
        match = re.search(r"FE\s:\s([A-z]+)", right_card_text)
        fe_allowed_str = right_card_text[match.regs[1][0]:match.regs[1][1]]
        is_allowed = fe_allowed_str == "Allowed"
        return is_allowed

    @staticmethod
    def get_most_recent_feedback(soup_html: BeautifulSoup) -> Optional[str]:
        div_cols = soup_html.select("#page-wrapper > div > div.col-lg-12.left > div > div > div")

        for div_col in div_cols:
            h4 = div_col.select_one("h4:nth-child(1)")
            if h4 and h4.text.strip() == "Feedback Ratings :":
                latest_feedback_span = div_col.select_one("span:nth-child(5)")
                if latest_feedback_span:
                    return latest_feedback_span.text
                else:
                    return None

        raise AssertionError("Could not find div with feedback.")

    @staticmethod
    def get_external_market_ratings(soup_html: BeautifulSoup) -> Tuple[
        Tuple[str, int, float, float, int, int, int, str]]:
        div_cols = soup_html.select("#page-wrapper > div > div.col-lg-12.left > div > div > div")
        external_market_verifications: List[Tuple[str, int, float, float, int, int, int, str]] = []
        div_col: BeautifulSoup
        for div_col in div_cols:
            h4 = div_col.select_one("h4:nth-child(1)")
            div_with_ratings = div_col.select_one("div:nth-child(2)")
            if h4 and h4.text.strip() == "Imported Feedback :" and div_with_ratings:
                rating_lines = [s.strip() for s in str(div_with_ratings).split("<p></p>")[1:]]
                remaining_external_market_ratings = list(APOLLON_MARKET_EXTERNAL_MARKET_STRINGS)
                for rating_line in rating_lines:
                    match = re.search(r"images\/([A-Za-z0-9]+)\.[A-Za-z0-9]{0,4}", rating_line)
                    market_handle = rating_line[match.regs[1][0]:match.regs[1][1]]
                    for market_id, market_string in remaining_external_market_ratings:
                        if market_handle == market_string:
                            rating_line_soup = BeautifulSoup(rating_line)
                            rating_tuple_str = rating_line_soup.text.strip()[1:].strip()
                            nr_match = re.search(r"[0-9]", rating_tuple_str)
                            if nr_match:
                                external_rating_tuple = get_external_rating_tuple(market_id, rating_tuple_str)
                                external_market_verifications.append(external_rating_tuple)
                            remaining_external_market_ratings.remove((market_id, market_string))
                            break

        return tuple(external_market_verifications)

    @staticmethod
    def get_feedback_categories_and_urls(soup_html: BeautifulSoup) -> Tuple[Tuple[str], Tuple[str]]:
        tab_links = soup_html.select("#page-wrapper > div > div.col-lg-12.left > ul > li > a")
        assert len(tab_links) == 5
        categories: List[str] = []
        urls: List[str] = []
        for link in tab_links[1:-1]:
            link: BeautifulSoup
            category = link.text.strip().split()[0]
            url = f"/{link['href']}"
            categories.append(category)
            urls.append(url)
        return tuple(categories), tuple(urls)

    @staticmethod
    def get_pgp_url(soup_html: BeautifulSoup) -> str:
        pgp_link = soup_html.select_one("#page-wrapper > div > div.col-lg-12.left > ul > li:nth-child(5) > a")
        assert pgp_link is not None
        return f"/{pgp_link['href']}"

    @staticmethod
    def get_feedbacks(soup_html: BeautifulSoup) -> Tuple[Tuple[datetime.datetime, str, str, str, str, str, float, str]]:
        feedbacks: List[Tuple[datetime.datetime, str, str, str, str, str, float, str]] = []

        table_rows = soup_html.select(
            "#page-wrapper > div > div.col-lg-12.left > div.tab-content > div > div > div > div > div > table > tbody "
            "> tr ")

        for row in table_rows:
            _, msg_and_title_td, buyer_td, price_td, date_td = row.select("td")
            msg = msg_and_title_td.select_one("small").text.strip()
            title = msg_and_title_td.select_one("sub").text.strip()
            buyer = buyer_td.select_one("small > a").text.strip()
            currency = "USD"
            price = price_td.select_one("small").text.strip()
            date_small_text = date_td.select_one("small").text.strip()
            match = re.search(r"[A-Z][a-z]{2}\s[0-9]{2},\s[0-9]{4}\s[0-2][0-9]:[0-5][0-9]", date_small_text)
            publication_date = dateparser.parse(date_small_text[match.regs[0][0]:match.regs[0][1]])
            text_hash = hashlib.md5(
                msg.encode(MD5_HASH_STRING_ENCODING)
            ).hexdigest()[:FEEDBACK_TEXT_HASH_COLUMN_LENGTH]
            url = f'/{date_td.select_one("small > a")["href"]}'
            feedbacks.append((publication_date, title, msg, text_hash, buyer, currency, price, url))
        return tuple(feedbacks)

    @staticmethod
    def get_next_feedback_url(soup_html: BeautifulSoup) -> Optional[str]:
        pagination_lis = soup_html.select(
            "#page-wrapper > div > div.col-lg-12.left > div.tab-content > div > div > div > div > ul > li")
        if not pagination_lis:
            return None
        for i in range(len(pagination_lis)):
            if "active" in pagination_lis[i].attrs["class"]:
                next_pagination_li = pagination_lis[i + 1]
                if next_pagination_li.text == "»":
                    return None
                else:
                    a_tag = next_pagination_li.select_one("a")
                    return f'/{a_tag["href"]}'

        raise AssertionError("No active pagination button.")

    @staticmethod
    def get_pgp_key(soup_html: BeautifulSoup) -> Optional[str]:
        pre = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div.tab-content > div > div > div > div > div > pre")
        if pre:
            return pre.text
        else:
            return None

    @staticmethod
    def get_is_seller(soup_html: BeautifulSoup) -> bool:
        right_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-2")
        assert right_card is not None
        right_card_text = right_card.text
        match = re.search(r"User\sType\s:\s([A-z]+)", right_card_text)
        user_type = right_card_text[match.regs[1][0]:match.regs[1][1]]
        if user_type == "Buyer":
            is_seller = False
        elif user_type == "Seller":
            is_seller = True
        else:
            raise AssertionError(f"Unknown user type '{user_type}'.")
        return is_seller

    @staticmethod
    def get_autofinalized_orders(soup_html: BeautifulSoup) -> int:
        right_card = soup_html.select_one(
            "#page-wrapper > div > div.col-lg-12.left > div:nth-child(1) > div > div > div.col-sm-2")
        assert right_card is not None
        right_card_text = right_card.text
        match = re.search(r"AutoFinalized\sOrders\s:\s([0-9]+)", right_card_text)
        nr_of_autofinalized_orders = parse_int(right_card_text[match.regs[1][0]:match.regs[1][1]])
        return nr_of_autofinalized_orders
