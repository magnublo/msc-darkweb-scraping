import re
from math import ceil
from typing import Tuple, Set, List

from bs4 import BeautifulSoup

from src.base.base_functions import BaseFunctions
from src.utils import parse_int


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
        category_search_select: BeautifulSoup = soup_html.select_one(
            "#wrapper > div.navbar-default.sidebar > div:nth-child(2) > div.panel-body > form > fieldset > div > div "
            "> select:nth-child(9)")

        assert category_search_select["name"] == 'ss_subcat'

        category_id_tuples = [o.attrs["value"] for o in category_search_select.select("option") if "value" in o.attrs]

        parent_sub_categories_index_urls: Set[str] = set()
        main_categories_index_urls: Set[str] = set()

        # example url: http://apollon2tclejj73.onion/home.php?cid=1&csid=1
        for category_id_tuple in category_id_tuples:
            c_id, sc_id, ssc_id = [int(s) for s in category_id_tuple.split("|")]
            if len({c_id, sc_id, ssc_id}) == 3:  # if all three IDs are different from each other
                parent_sub_categories_index_urls.add(
                    f"/home.php?cid={c_id}&csid={sc_id}")  # then we are talking about a parent sub category
            main_categories_index_urls.add(f"/home.php?cid={c_id}")

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
                page_url_in_category = f"{sub_sub_category_url}&ss_home=2&pg={k+1}"
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
                page_url_in_category = f"{parent_sub_category_url}&ss_home=2&pg={k+1}"
                tasks.append((category, page_url_in_category))

        return tuple(tasks)

    @staticmethod
    def get_sub_sub_categories_urls_and_nrs_of_listings(soup_html: BeautifulSoup) -> Tuple[Tuple[Tuple, str, int]]:
        sub_sub_category_hrefs = soup_html.select("#side-menu > ul > li > ul > li > a")
        sub_sub_categories_urls_and_nrs_of_listings: List[Tuple[Tuple, str, int]] = []

        a: BeautifulSoup
        for a in sub_sub_category_hrefs:
            stripped_text = a.text.strip()
            match = re.match(r"^(.+)\s*\[(\s*[0-9]+\s*)\]$", stripped_text)
            assert match
            category_name = stripped_text[match.regs[1][0]:match.regs[1][1]].strip()
            parent_category_name = ApollonScrapingFunctions.get_currently_selected_parent_sub_category(soup_html)
            category = (category_name, None, parent_category_name, 2)
            nr_of_listings = parse_int(stripped_text[match.regs[2][0]:match.regs[2][1]].strip())
            sub_sub_categories_urls_and_nrs_of_listings.append((category, a["href"], nr_of_listings))

        return tuple(sub_sub_categories_urls_and_nrs_of_listings)

    @staticmethod
    def get_parent_sub_category_urls_and_nrs_of_listings(soup_html: BeautifulSoup) -> Tuple[Tuple[None, str, int]]:
        parent_sub_category_hrefs = soup_html.select("#side-menu > ul > li > a")
        # #side-menu > ul:nth-child(4) > li > a
        parent_sub_categories_urls_and_nrs_of_listings: List[Tuple[None, str, int]] = []

        a: BeautifulSoup
        for a in parent_sub_category_hrefs:
            stripped_text = a.text.strip()
            match = re.match(r"^(.+)\s*\[(\s*[0-9]+\s*)\]$", stripped_text)
            assert match
            nr_of_listings = parse_int(stripped_text[match.regs[2][0]:match.regs[2][1]].strip())
            parent_sub_categories_urls_and_nrs_of_listings.append((None, a["href"], nr_of_listings))

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
                match = re.match(r"^(.+)\s*\[(\s*[0-9]+\s*)\]$", stripped_text)
                assert match
                return stripped_text[match.regs[1][0]:match.regs[1][1]].strip()

        raise AssertionError("Could not determine which main category is selected in sidebar.")

    @staticmethod
    def get_currently_selected_parent_sub_category(soup_html: BeautifulSoup) -> str:
        all_sub_categories = soup_html.select("#side-menu > ul")
        for sub_category in all_sub_categories[:-1]:
            sub_category: BeautifulSoup
            sub_li = sub_category.select_one("li")
            sub_uls = sub_li.select("ul")
            if len(sub_uls) > 0:
                stripped_text = sub_category.text.strip().split("\n", maxsplit=1)[0].strip()
                match = re.match(r"^(.+)\s*\[(\s*[0-9]+\s*)\]$", stripped_text)
                assert match
                return stripped_text[match.regs[1][0]:match.regs[1][1]].strip()

        raise AssertionError("Could not determine which parent sub category is selected in sidebar.")

    @staticmethod
    def get_listing_infos(soup_html: BeautifulSoup):
        # product_page_urls, urls_is_sticky, titles, sellers, seller_urls, nrs_of_views
        pass
