import hashlib
from multiprocessing import Queue
from random import shuffle
from typing import List

import cfscrape
import requests

from definitions import CRYPTONIA_MARKET_CATEGORY_INDEX, CRYPTONIA_MARKET_BASE_URL, \
    CRYPTONIA_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE, PYTHON_SIDE_ENCODING
from src.base_scraper import BaseScraper
from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions
from src.db_utils import get_column_name
from src.models.scraping_session import ScrapingSession
from src.utils import get_page_as_soup_html


class CryptoniaScrapingSession(BaseScraper):

    def __init__(self, queue: Queue, username: str, password: str, nr_of_threads: int, thread_id: int, proxy: dict,
                 session_id: int = None):
        super().__init__(queue, username, password, nr_of_threads, thread_id=thread_id, proxy=proxy, session_id=session_id)

    def _get_web_session(self) -> requests.Session:
        return cfscrape.Session()

    def populate_queue(self) -> None:
        web_response = self._get_logged_in_web_response(CRYPTONIA_MARKET_CATEGORY_INDEX)
        soup_html = get_page_as_soup_html(self.working_dir, web_response)
        category_lists, category_base_urls = \
            scrapingFunctions.get_category_lists_and_urls(soup_html)
        task_list = []

        for category_list, category_base_url in zip(category_lists, category_base_urls):
            web_response = self._get_logged_in_web_response(f"{CRYPTONIA_MARKET_BASE_URL}/{category_base_url}")
            soup_html = get_page_as_soup_html(self.working_dir, web_response)
            nr_of_pages = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
            task_list.append([category_list, category_base_url])
            for k in range(1, nr_of_pages):
                task_list.append((category_list, f"{category_base_url}/{k+1}"))

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def _scrape_queue_item(self, category_list: List[str], search_result_url: str) -> None:
        web_response = self._get_logged_in_web_response(search_result_url)

        soup_html = get_page_as_soup_html(self.working_dir, web_response)

        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)

        if len(product_page_urls) == 0:
            if soup_html.text.find(CRYPTONIA_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE) == -1:
                raise AssertionError  # raise error if no logical reason why search result is empty
            else:
                return

        btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)

        assert len(titles) == len(sellers) == len(seller_urls) == len(product_page_urls)

        for title, seller_name, seller_url, product_page_url in zip(titles, sellers, seller_urls,
                                                                    product_page_urls):
            self._db_error_catch_wrapper(title, seller_name, seller_url, product_page_url,
                                         btc_rate, xmr_rate, func=self._scrape_listing)

    def _scrape_listing(self, title: str, seller_name: str, seller_url: str, product_page_url: str, btc_rate: float,
                        xmr_rate: float):

        seller, is_new_seller = self._get_seller(seller_name)

        listing_observation, is_new_listing_observation = self._get_listing_observation(title, seller.id)

        if not is_new_listing_observation:
            return

        is_new_seller_observation = self._exists_seller_observation_from_this_session(seller.id)

        if is_new_seller_observation:
            self._scrape_seller(seller_url, seller, is_new_seller)

        self.print_crawling_debug_message(url=product_page_url)

        web_response = self._get_logged_in_web_response(product_page_url)
        soup_html = get_page_as_soup_html(self.working_dir, web_response)

        listing_text = scrapingFunctions.get_description(soup_html)
        listing_text_id = hashlib.md5(listing_text.encode(PYTHON_SIDE_ENCODING)).hexdigest()
        categories, website_category_ids = scrapingFunctions.get_categories_and_ids(soup_html)
        accepts_BTC, accepts_LTC, accepts_XMR = scrapingFunctions.accepts_currencies(soup_html)
        nr_sold, nr_sold_since_date = scrapingFunctions.get_nr_sold_since_date(soup_html)
        fiat_currency, price = scrapingFunctions.get_fiat_currency_and_price(soup_html)
        origin_country, destination_countries, payment_type = \
            scrapingFunctions.get_origin_country_and_destinations_and_payment_type(
                soup_html)

        self._add_category_junctions(categories, website_category_ids, listing_observation.id)

        self.db_session.merge(ListingText(
            id=listing_text_id,
            text=listing_text
        ))

        self.db_session.merge(Country(
            id=origin_country
        ))

        self._add_country_junctions(destination_countries, listing_observation.id)

        listing_observation.listing_text_id = listing_text_id
        listing_observation.btc = accepts_BTC
        listing_observation.ltc = accepts_LTC
        listing_observation.xmr = accepts_XMR
        listing_observation.nr_sold = nr_sold
        listing_observation.nr_sold_since_date = nr_sold_since_date
        listing_observation.promoted_listing = is_sticky
        listing_observation.url = product_page_url
        listing_observation.btc_rate = btc_rate
        listing_observation.ltc_rate = ltc_rate
        listing_observation.xmr_rate = xmr_rate
        listing_observation.fiat_currency = fiat_currency
        listing_observation.price = price
        listing_observation.origin_country = origin_country
        listing_observation.payment_type = payment_type

        self.db_session.flush()



    def _login_and_set_cookie(self, response=None) -> None:
        pass

    def _get_market_URL(self) -> str:
        pass

    def _get_market_ID(self) -> str:
        pass

    def _get_working_dir(self) -> str:
        pass

    def _get_headers(self) -> dict:
        pass

    def _set_cookies(self) -> None:
        pass

    def _get_login_url(self) -> str:
        pass

    def _get_login_phrase(self) -> str:
        pass
