import re
from typing import Tuple, Dict, List

from bs4 import BeautifulSoup

from src.base.base_functions import BaseFunctions
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
            #body > div.main > div.content > div > form > table > tbody > tr:nth-child(1) > td:nth-child(1) > label
        return "Bitcoin (BTC)" in currency_strs, "Bitcoin Cash (BCH)" in currency_strs, "Monero (XMR)" in currency_strs

    @staticmethod
    def get_price_and_currency(soup_html: BeautifulSoup) -> Tuple[float, str]:
        price_phrase = soup_html.select_one("body > div.main > div.content > div > div.tabularDetails > div:nth-child(2) > span").text
        #                                   body > div.main > div.content > div > div.tabularDetails > div: nth - child(2) > span
        currency = infer_currency_from_symbol(price_phrase[0])
        match = re.search(r"(?:฿|\$|€)([0-9]+\.[0-9]+)(?:\s\(\$[0-9]+\.[0-9]+\))?", price_phrase)
        start_index = match.regs[1][0]
        end_index = match.regs[1][1]
        price = parse_float(price_phrase[start_index:end_index])
        return price, currency
    #฿([0-9]+\.[0-9]+)\s\(\$[0-9]+\.[0-9]+\)
    # body > div.main > div.content > div > div.tabularDetails > div:nth-child(2) > span

    @staticmethod
    def get_fiat_exchange_rates(soup_html: BeautifulSoup) -> Dict[str, float]:
        exchange_rates_header = soup_html.select_one("body > div.main > div.sidebar.right > div:nth-child(3) > div.sidebarHeader")
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
        ships_from_div = soup_html.select_one("body > div.main > div.content > div > div.tabularDetails > div:nth-child(4)")
        ships_from_label = ships_from_div.select_one("label")
        ships_from_span = ships_from_div.select_one("span")

        assert ships_from_label.text.strip().lower() == "ships from"
        origin_country = ships_from_span.text.strip()
        assert len(origin_country) > 0
        return origin_country

    @staticmethod
    def get_destination_countries(soup_html: BeautifulSoup) -> Tuple[str, ...]:
        ships_to_div = soup_html.select_one("body > div.main > div.content > div > div.tabularDetails > div:nth-child(3)")
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
        pass
