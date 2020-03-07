import datetime
import re
from typing import Tuple, Dict, List, Optional, Union

from bs4 import BeautifulSoup

from definitions import DREAM_MARKET_EXTERNAL_MARKET_STRINGS
from src.base.base_functions import BaseFunctions, get_external_rating_tuple
from src.db_utils import shorten_and_sanitize_for_text_column
from src.utils import parse_float


def infer_currency_from_symbol(symbol: str) -> str:
    if symbol == "฿":
        return "BTC"
    elif symbol == "$":
        return "USD"
    elif symbol == "€":
        return "EUR"
    elif symbol == "£":
        return "GBP"
    else:
        raise AssertionError("Unknown currency")


def get_div_depth(category_div: BeautifulSoup) -> int:
    for html_class in category_div.attrs.get("class"):
        s = html_class.strip()
        if s[:5] == "depth":
            return int(s[5])
    raise AssertionError("Could not determine depth.")


def get_category_info_from_div(category_div: BeautifulSoup) -> Tuple[str, int]:
    # return name and marketside id
    a_tag = category_div.select_one("a")
    return " ".join(a_tag.text.strip().split()[:-1]), int(a_tag["href"].rsplit("=", maxsplit=1)[-1])


def get_messaging_div_text(soup_html: BeautifulSoup, headline_phrase: str) -> str:
    messaging_tab_divs = soup_html.select(
        "body > div.main.onlyLeftNavLayout > div.content > div > div.messagingTab > div")
    for div in messaging_tab_divs:
        subtitle_div = div.select_one("div.subtitle")
        subtitle_text = subtitle_div.text.strip()
        if subtitle_text.lower() == headline_phrase:
            return shorten_and_sanitize_for_text_column(div.select_one("div.preformattedNotes > pre").text.strip())


def get_username_span(soup_html: BeautifulSoup) -> BeautifulSoup:
    user_profile_table = soup_html.select_one(
        "body > div.main.onlyLeftNavLayout > div.content > div > div.paddingOnRight > div.profileNotes.tabularDetails > div:nth-child(1) > table")

    username_span = user_profile_table.select_one("tr > td:nth-child(2) > span")
    return username_span if username_span else user_profile_table.select_one(
        "tbody > tr > td:nth-child(2) > span")


def str_is_in_element_classes(html_element: BeautifulSoup, string: str):
    for html_class in html_element.attrs.get("class"):
        if html_class.find(string) != -1:
            return True
    return False


class DreamScrapingFunctions(BaseFunctions):

    @staticmethod
    def is_logged_in(soup_html: BeautifulSoup, username: str) -> bool:
        raise NotImplementedError('')

    @staticmethod
    def get_captcha_image_url_from_market_page(soup_html: BeautifulSoup) -> str:
        raise NotImplementedError('')

    @staticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:
        raise NotImplementedError('')

    @staticmethod
    def get_meta_refresh_interval(soup_html: BeautifulSoup) -> Tuple[int, str]:
        raise NotImplementedError('')

    @staticmethod
    def get_captcha_instruction(soup_html: BeautifulSoup) -> str:
        raise NotImplementedError('')

    def _format_logger_message(self, message: str) -> str:
        raise NotImplementedError('')

    @staticmethod
    def page_is_listing(soup_html: BeautifulSoup) -> bool:
        return soup_html.select_one("body > div.main > div.content > div > div.tabularDetails") is not None

    @staticmethod
    def page_is_seller(soup_html: BeautifulSoup) -> bool:
        links = soup_html.select(
            "body > div.main.onlyLeftNavLayout > div.content > div > div.paddingOnRight > div.rightAlign > div > a")
        for link in links:
            if link is not None and link.text.lower().strip() == "report vendor":
                return True

    @staticmethod
    def page_is_search_result(soup_html: BeautifulSoup) -> bool:
        return soup_html.select_one(
            "body > div.main.onlyLeftNavLayout > div.content > div.shop > div:nth-child(4) > div:nth-child(1)") is not None

    @staticmethod
    def page_is_login_page(soup_html: BeautifulSoup) -> bool:
        login_button = soup_html.select_one(
            "body > div.main > div.naviHeader.oldBannerImage > div > div > ul > li.active > a")
        # body > div.main > div.naviHeader.oldBannerImage > div > div > ul > li.active > a
        return login_button is not None and login_button.text.lower().strip() == "login"

    @staticmethod
    def page_is_ddos_protection(soup_html: BeautifulSoup) -> bool:
        title = soup_html.select_one(
            "body > div > form > div.ddos")
        return title is not None and title.text.lower().strip() == "ddos protection"

    @staticmethod
    def page_is_main_page(soup_html: BeautifulSoup) -> bool:
        market_link = soup_html.select_one(
            "body > div.main > div.content > div > div.actionContainer > a")
        return market_link is not None and market_link.text.lower().strip() == "proceed to market"

    # body > div.main > div.content > div > div.actionContainer > a

    @staticmethod
    def page_is_not_found_error(soup_html: BeautifulSoup) -> bool:
        page_title = soup_html.select_one(
            "head > title")
        return page_title is not None and " ".join(page_title.text.strip().split()[-2:]).lower() in (
            "not found", "has occured")

    # head > title

    @staticmethod
    def get_seller_name_from_listing(soup_html: BeautifulSoup) -> str:
        name = soup_html.select_one(
            "body > div.main > div.content > div > div.tabularDetails > div:nth-child(1) > span > a:nth-child(1)").text.strip()
        assert name.find("(") == -1 and len(name) > 0
        return name

    @staticmethod
    def accepts_currencies(soup_html: BeautifulSoup) -> Tuple[bool, bool, bool]:
        currency_strs = [s.text.strip() for s in soup_html.select(
            "body > div.main > div.content > div > form > table > tbody > tr > td:nth-child(1) > label")]
        # body > div.main > div.content > div > form > table > tbody > tr:nth-child(1) > td:nth-child(1) > label
        return "Bitcoin (BTC)" in currency_strs, "Bitcoin Cash (BCH)" in currency_strs, "Monero (XMR)" in currency_strs

    @staticmethod
    def get_price_and_currency(soup_html: BeautifulSoup) -> Tuple[float, str]:
        price_phrase = soup_html.select_one(
            "body > div.main > div.content > div > div.tabularDetails > div:nth-child(2) > span").text
        #                                   body > div.main > div.content > div > div.tabularDetails > div: nth - child(2) > span
        currency = infer_currency_from_symbol(price_phrase[0])
        match = re.search(r"(?:฿|\$|€)([0-9]+\.[0-9]+)(?:\s\(\$[0-9]+\.[0-9]+\))?", price_phrase)
        start_index = match.regs[1][0]
        end_index = match.regs[1][1]
        price = parse_float(price_phrase[start_index:end_index])
        return price, currency

    # ฿([0-9]+\.[0-9]+)\s\(\$[0-9]+\.[0-9]+\)
    # body > div.main > div.content > div > div.tabularDetails > div:nth-child(2) > span

    @staticmethod
    def get_fiat_exchange_rates(soup_html: BeautifulSoup) -> Dict[str, float]:
        exchange_rates_header = soup_html.select_one(
            "body > div.main > div.sidebar.right > div:nth-child(3) > div.sidebarHeader")
        assert exchange_rates_header.text.strip()[0] == "฿"

        exchange_rates: Dict[str, float] = {}
        rate_rows = [" ".join(r.text.strip().split()) for r in soup_html.select(
            "body > div.main > div.sidebar.right > div:nth-child(3) > div.exchangeRateListing > table > tbody > tr")]

        if not rate_rows:
            rate_rows = [" ".join(r.text.strip().split()) for r in soup_html.select(
                "body > div.main > div.sidebar.right > div:nth-child(3) > div.exchangeRateListing > table > tr")]

        for row in rate_rows:
            currency, rate_str = row.split()
            exchange_rates[currency] = parse_float(rate_str)

        return exchange_rates

    @staticmethod
    def get_origin_country(soup_html: BeautifulSoup) -> str:
        ships_from_div = soup_html.select_one(
            "body > div.main > div.content > div > div.tabularDetails > div:nth-child(4)")
        ships_from_label = ships_from_div.select_one("label")
        ships_from_span = ships_from_div.select_one("span")

        assert ships_from_label.text.strip().lower() == "ships from"
        origin_country = ships_from_span.text.strip()
        assert len(origin_country) > 0
        return origin_country

    @staticmethod
    def get_destination_countries(soup_html: BeautifulSoup) -> Tuple[str, ...]:
        ships_to_div = soup_html.select_one(
            "body > div.main > div.content > div > div.tabularDetails > div:nth-child(3)")
        ships_to_label = ships_to_div.select_one("label")
        ships_to_span = ships_to_div.select_one("span")

        assert ships_to_label.text.strip().lower() == "ships to"
        dest_countries_str = ships_to_span.text.strip()
        destination_countries: List[str] = [dest_countries_str[a.regs[0][0]:a.regs[0][1]].strip() for a in
                                            BaseFunctions.COMMA_SEPARATED_COUNTRY_REGEX.finditer(dest_countries_str)]
        return tuple(destination_countries)

    @staticmethod
    def get_has_escrow(soup_html: BeautifulSoup) -> bool:
        escrow_div = soup_html.select_one("body > div.main > div.content > div > div.tabularDetails > div:nth-child(5)")
        escrow_label = escrow_div.select_one("label")
        escrow_span = escrow_div.select_one("span")
        has_escrow_str = escrow_span.text.strip().lower()

        assert escrow_label.text.strip().lower() == "escrow"

        if has_escrow_str == "yes":
            return True
        elif has_escrow_str == "no":
            return False
        else:
            raise AssertionError("Neither yes nor no on whether listing supports escrow")

    @staticmethod
    def get_shipping_methods(soup_html: BeautifulSoup) -> Tuple[Tuple[str, None, str, float, None, None]]:
        shipping_methods: List[Tuple[str, None, str, float, None, None]] = []
        # description, days_shipping_time, fiat_currency, price, quantity_unit_name, price_is_per_unit
        try:
            shipping_methods_table = soup_html.select("body > div.main > div.content > div > form > table")[-2]
        except IndexError:
            return tuple()
        shipping_method_rows = shipping_methods_table.select("tbody > tr")
        for row in shipping_method_rows:
            price_td, description_td, _ = row.select("td")
            price_str = " ".join(price_td.text.strip().split())
            description = " ".join(description_td.text.strip().split())
            currency = infer_currency_from_symbol(price_str[0])
            price = parse_float(price_str[1:])
            shipping_methods.append((description, None, currency, price, None, None))

        return tuple(shipping_methods)

    @staticmethod
    def get_listing_text(soup_html: BeautifulSoup) -> str:
        listing_text_pre = soup_html.select_one("#offerDescription > pre")
        assert listing_text_pre is not None
        listing_text = listing_text_pre.text.strip()
        assert len(listing_text) > 0
        return listing_text

    @staticmethod
    def get_listing_title(soup_html: BeautifulSoup) -> str:
        title: str = soup_html.select_one("body > div.main > div.content > div > div.title").text.strip()
        assert len(title) > 0
        return title

    @staticmethod
    def get_categories(soup_html: BeautifulSoup) -> Tuple[Tuple[str, int, Optional[str], int], ...]:
        # each element has name, marketside_id, parent_name and level
        parentless_categories: List[Tuple[str, int, int]] = []
        listing_categories: List[Tuple[str, int, Optional[str], int]] = []
        category_divs = soup_html.select("body > div.main > div.sidebar.browse > div")

        category_div: BeautifulSoup
        name: str
        marketside_id: int

        for i, category_div in enumerate(reversed(category_divs)):
            if "selected" in category_div.attrs.get("class"):
                selected_depth: int = get_div_depth(category_div)
                name, marketside_id = get_category_info_from_div(category_div)
                parentless_categories.append((name, marketside_id, selected_depth))
                previous_depth = selected_depth
                for unselected_category_div in reversed(category_divs[:-(i + 1)]):
                    html_classes = unselected_category_div.attrs.get("class")
                    if "category" not in html_classes:
                        break
                    depth: int = get_div_depth(unselected_category_div)
                    if depth < previous_depth:
                        name, marketside_id = get_category_info_from_div(unselected_category_div)
                        parentless_categories.append((name, marketside_id, depth))
                    previous_depth = depth
                break

        for i, category in enumerate(parentless_categories[:-1]):
            # starting with deepest subcategory
            parent_name = parentless_categories[i + 1][0]
            listing_categories.append((category[0], category[1], parent_name, category[2]))

        listing_categories.append(
            (parentless_categories[-1][0], parentless_categories[-1][1], None, parentless_categories[-1][2]))

        return tuple(listing_categories)

    @staticmethod
    def get_seller_name(soup_html: BeautifulSoup) -> str:
        username_span = get_username_span(soup_html)
        username = username_span.text.strip().split()[0]
        assert len(username) > 0
        return username

    @staticmethod
    def get_terms_and_conditions(soup_html: BeautifulSoup) -> str:
        return get_messaging_div_text(soup_html, "terms and conditions")

    @staticmethod
    def get_pgp_key(soup_html: BeautifulSoup) -> str:
        return get_messaging_div_text(soup_html, "public pgp key")

    @staticmethod
    def get_number_of_sales_and_rating(soup_html: BeautifulSoup) -> Union[Tuple[int, float], Tuple[None, None]]:
        username_span = get_username_span(soup_html)
        a_tags = username_span.select("a")
        assert len(a_tags) <= 1
        a_tag = a_tags[0]
        a_tag_text = a_tag.text.strip()

        match = re.search(r"[^\s]+\s\(([0-9]+)\)\s?\(([0-9\.\s]+)\)", a_tag_text)
        if match:
            start_index_sales_str = match.regs[1][0]
            end_index_sales_str = match.regs[1][1]
            sales_str = a_tag_text[start_index_sales_str:end_index_sales_str]

            start_index_rating_str = match.regs[2][0]
            end_index_rating_str = match.regs[2][1]
            rating_str = a_tag_text[start_index_rating_str:end_index_rating_str]

            return int(sales_str), float(rating_str)
        else:
            return None, None

    @staticmethod
    def get_last_online(soup_html: BeautifulSoup) -> datetime:
        profile_divs = soup_html.select(
            "body > div.main.onlyLeftNavLayout > div.content > div > div.paddingOnRight > div.profileNotes.tabularDetails > div")

        for profile_div in reversed(profile_divs):
            profile_div_span = profile_div.select_one("span")
            if profile_div_span.text.strip().lower() == "last active":
                profile_div_label_text = profile_div.select_one("label").text.strip()
                day, month, year = [int(i) for i in profile_div_label_text.split()[0].split("/")]
                return datetime.datetime(day=day, month=month, year=year)

        raise AssertionError("Could not determine last online date")

    @staticmethod
    def get_registration_date(soup_html: BeautifulSoup) -> datetime:
        profile_divs = soup_html.select(
            "body > div.main.onlyLeftNavLayout > div.content > div > div.paddingOnRight > div.profileNotes.tabularDetails > div")

        for profile_div in reversed(profile_divs)[1:]:
            profile_div_span = profile_div.select_one("span")
            if profile_div_span.text.strip().lower() == "join date":
                profile_div_label_text = profile_div.select_one("label").text.strip()
                day, month, year = [int(i) for i in profile_div_label_text.split()[0].split("/")]
                return datetime.datetime(day=day, month=month, year=year)

        raise AssertionError("Could not determine registration date")

    @staticmethod
    def get_fe_enabled(soup_html: BeautifulSoup) -> bool:
        profile_divs = soup_html.select(
            "body > div.main.onlyLeftNavLayout > div.content > div > div.paddingOnRight > div.profileNotes.tabularDetails > div")

        for profile_div in reversed(profile_divs)[2:]:
            profile_div_span = profile_div.select_one("span")
            if profile_div_span.text.strip().lower() == "fe enabled":
                profile_div_label_text = profile_div.select_one("label").text.strip().lower()
                if profile_div_label_text == "yes":
                    return True
                elif profile_div_label_text == "no":
                    return False
                else:
                    raise AssertionError("fe enabled was neither yes nor no.")

        raise AssertionError("Could not determine fe enabled")

    @staticmethod
    def get_external_market_ratings(soup_html: BeautifulSoup) -> Tuple[
        Tuple[str, int, float, float, int, int, int, str]]:
        external_market_verifications: List[Tuple[str, int, float, float, int, int, int, str]] = []

        username_span = get_username_span(soup_html)
        rating_spans: Tuple[BeautifulSoup, ...] = username_span.select("span")
        remaining_external_market_ratings = list(DREAM_MARKET_EXTERNAL_MARKET_STRINGS)
        if len(rating_spans) > 2:
            for rating_span in rating_spans[2:]:
                for market_id, market_string in remaining_external_market_ratings:
                    if str_is_in_element_classes(html_element=rating_span, string=market_string):
                        rating_tuple_str = rating_span.text.strip()
                        external_rating_tuple = get_external_rating_tuple(market_id, rating_tuple_str)
                        external_market_verifications.append(external_rating_tuple)
                        remaining_external_market_ratings.remove((market_id, market_string))
                        break

        return tuple(external_market_verifications)