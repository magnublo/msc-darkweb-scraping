import datetime
import os
import pickle
import re
from multiprocessing.queues import Queue
from threading import Lock
from time import time
from typing import Type, Dict, Tuple, List, Optional

import requests
from bs4 import BeautifulSoup
from requests import Response

from definitions import DREAM_MARKET_ID, DREAM_SRC_DIR
from src.base.base_functions import BaseFunctions
from src.base.base_logger import BaseClassWithLogger
from src.base.base_scraper import BaseScraper
from src.db_utils import get_engine, get_db_session
from src.dream.dream_functions import DreamScrapingFunctions
from src.models.listing_observation import ListingObservation
from src.models.seller import Seller
from src.utils import PageType, get_page_as_soup_html


def get_usd_price_from_rates(price: float, currency: str, fiat_exchange_rates: Dict[str, float]) -> float:
    if currency == "USD":
        return price
    else:
        btc_price = price / fiat_exchange_rates[currency]
        return btc_price * fiat_exchange_rates["USD"]


def process_shipping_methods(unprocessed_shipping_methods: Tuple[Tuple[str, None, str, float, None, None]],
                             fiat_exchange_rates: Dict[str, float]) -> Tuple[Tuple[str, None, str, float, None, None]]:
    shipping_methods: List[Tuple[str, None, str, float, None, None]] = []
    for description, _, currency, price, _, _ in unprocessed_shipping_methods:
        usd_price = get_usd_price_from_rates(price, currency, fiat_exchange_rates)
        shipping_methods.append((description, None, "USD", usd_price, None, None))

    return tuple(shipping_methods)


class PageMetadata:

    def __init__(self, meta_data_dict: Dict):
        self.created_date: datetime = datetime.datetime.now()
        raise NotImplementedError('')


class DreamScrapingSession(BaseScraper, BaseClassWithLogger):

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int, proxy: dict, session_id: int):
        self.proxy_port = 0000
        BaseClassWithLogger.__init__(self)
        self.engine = get_engine()
        self.url_failure_counts: Dict[str, int] = {}
        self.pages_counter = 0
        self.failed_captcha_counter = 0
        self.scraping_funcs = self._get_scraping_funcs()
        self.working_dir = self._get_working_dir()
        self.db_session = get_db_session(self.engine)
        self.thread_id = thread_id
        self.nr_of_threads = nr_of_threads
        self.queue = queue
        self.market_id = self._get_market_id()
        self.duplicates_this_session = 0
        self.initial_queue_size = self.queue.qsize()
        self.session_id = session_id or self._initiate_session()
        self.START_TIME = time()
        self.user_credentials_db_lock = None
        self.scraping_funcs = self._get_scraping_funcs()

    def _handle_custom_server_error(self) -> None:
        return

    def _get_market_id(self) -> str:
        return DREAM_MARKET_ID

    def _get_working_dir(self) -> str:
        return DREAM_SRC_DIR

    def _get_headers(self) -> dict:
        return {}

    def _get_login_url(self) -> str:
        return ""

    def _get_is_logged_out_phrase(self) -> str:
        return "sdwaed"

    def populate_queue(self) -> None:
        dir_path = f"{os.getenv('DREAM_HTML_DIR')}"
        files = os.listdir(dir_path)

        for file in [f for f in files if re.match(r"[0-9]{13}_[0-9]{4}_[a-z0-9]{40}\.html", f)]:
            self.queue.put((f"{dir_path}/{file}",))

        self.initial_queue_size = self.queue.qsize()

    def _get_web_session_object(self) -> requests.Session:
        raise NotImplementedError('')

    def _scrape_queue_item(self, file_path: str) -> None:

        with open(file_path, "r") as f:
            soup_html = get_page_as_soup_html(f.read())

        meta_file_path = file_path.rsplit(r".", maxsplit=1)[0] + r".meta"

        with open(meta_file_path, "r") as f:
            meta_data_dict: Dict = pickle.load(f)
            meta_data: PageMetadata = PageMetadata(meta_data_dict)

        if self.queue.qsize() % 500 == 0:
            self.logger.info(f"{self.queue.qsize()}/{self.initial_queue_size}")

        page_type: PageType = self._determine_page_type(soup_html)
        if page_type == PageType.LISTING:
            self._scrape_listing(soup_html, meta_data.created_date)
            pass
        elif page_type == PageType.SELLER:
            # self._scrape_seller(soup_html)
            pass

    def _scrape_listing(self, soup_html: BeautifulSoup, created_date: datetime) -> None:
        seller: Seller
        is_new_seller: bool
        listing_observation: ListingObservation
        is_new_listing_observation: bool
        is_new_seller_observation: bool
        web_response: requests.Response
        soup_html: BeautifulSoup
        listing_text: str
        listing_categories: Tuple[Tuple[str, int, Optional[str], Optional[int]]]
        website_category_ids: List[int]
        accepts_BTC: bool
        accepts_LTC: bool
        accepts_XMR: bool
        nr_sold: None
        nr_sold_since_date: datetime
        fiat_currency: str
        price: float
        origin_country: str
        destination_countries: Tuple[str]
        payment_type: str
        accepts_BTC_multisig: bool
        escrow: bool
        non_standardized_listing_type: str
        self.scraping_funcs: DreamScrapingFunctions

        shipping_methods: Tuple[Tuple[str, None, str, float, None, None]]

        seller_name: str = self.scraping_funcs.get_seller_name_from_listing(soup_html)
        seller, _ = self._get_seller(seller_name)
        title = self.scraping_funcs.get_listing_title(soup_html)

        fiat_exchange_rates: Dict[str, float] = self.scraping_funcs.get_fiat_exchange_rates(soup_html)
        price, currency = self.scraping_funcs.get_price_and_currency(soup_html)
        fiat_price = get_usd_price_from_rates(price, currency, fiat_exchange_rates)

        fiat_currency = "USD"
        accepts_BTC_multisig = False  # not supported on Dream
        ends_in = None  # no sign that Dream supports time limited listings
        fifty_percent_finalize_early = None  # no such feature on Dream
        quantity_in_stock = None  # no such field on Dream
        standardized_listing_type = None  # no listing type field on Dream

        accepts_BTC, accepts_BCH, accepts_XMR = self.scraping_funcs.accepts_currencies(soup_html)
        nr_sold = None
        origin_country = self.scraping_funcs.get_origin_country(soup_html)
        destination_countries = self.scraping_funcs.get_destination_countries(soup_html)
        escrow = self.scraping_funcs.get_has_escrow(soup_html)

        un_processed_shipping_methods = self.scraping_funcs.get_shipping_methods(soup_html)
        shipping_methods = process_shipping_methods(un_processed_shipping_methods, fiat_exchange_rates)

        listing_text = self.scraping_funcs.get_listing_text(soup_html)
        listing_text_id: int = self._add_text(listing_text)

        listing_observation = ListingObservation(thread_id=self.thread_id, created_date=created_date, session_id=self.session_id, listing_text_id=listing_text_id, title=ti)

        self._add_shipping_methods(listing_observation.id, shipping_methods)
        self._add_category_junctions(listing_observation.id, category_pair)



        country_ids: Tuple[int] = self._add_countries(origin_country, *destination_countries)
        destination_country_ids = country_ids[1:]
        self._add_country_junctions(destination_country_ids, listing_observation.id)

        listing_observation.title = title
        listing_observation.seller_id = seller.id
        listing_observation.listing_text_id = listing_text_id
        listing_observation.btc = accepts_BTC
        listing_observation.ltc = accepts_LTC
        listing_observation.xmr = accepts_XMR
        listing_observation.btc_multisig = accepts_BTC_multisig
        listing_observation.nr_sold = nr_sold
        listing_observation.nr_sold_since_date = publication_date
        listing_observation.promoted_listing = is_sticky
        listing_observation.url = product_url
        listing_observation.btc_rate = btc_rate
        listing_observation.ltc_rate = ltc_rate
        listing_observation.xmr_rate = xmr_rate
        listing_observation.fiat_currency = fiat_currency
        listing_observation.price = fiat_price
        listing_observation.origin_country = country_ids[0]
        listing_observation.escrow = escrow
        listing_observation.listing_type = standardized_listing_type.name
        listing_observation.quantity_in_stock = quantity_in_stock
        listing_observation.ends_in = ends_in
        listing_observation.nr_of_views = nr_of_views

        listing_observation.bch_rate = bch_rate
        listing_observation.bch = accepts_BCH
        listing_observation.fifty_percent_finalize_early = fifty_percent_finalize_early

        self.db_session.flush()

        with self.__current_tasks_lock__:
            self.CURRENT_TASKS.discard(product_url)

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        return DreamScrapingFunctions

    def _get_anti_captcha_kwargs(self):
        raise NotImplementedError('')

    def _is_logged_out(self, web_session: requests.Session, response: Response, login_url: str,
                       login_page_phrase: str) -> bool:
        raise NotImplementedError('')

    def _get_min_credentials_per_thread(self) -> int:
        raise NotImplementedError('')

    def _get_mirror_db_lock(self) -> Lock:
        raise NotImplementedError('')

    def _get_user_credentials_db_lock(self) -> Lock:
        raise NotImplementedError('')

    def _get_mirror_failure_lock(self) -> Lock:
        raise NotImplementedError('')

    def _is_custom_server_error(self, response) -> bool:
        raise NotImplementedError('')

    def _apply_processing_to_captcha_image(self, image_response, captcha_instruction):
        raise NotImplementedError('')

    def _captcha_instruction_is_generic(self, captcha_instruction: str) -> bool:
        raise NotImplementedError('')

    def _is_expected_page(self, response: requests.Response, expected_page_type: PageType) -> bool:
        return True

    def _get_captcha_image_request_headers(self, headers: dict) -> dict:
        raise NotImplementedError('')

    def _determine_page_type(self, soup_html: BeautifulSoup) -> PageType:
        self.scraping_funcs: DreamScrapingFunctions
        if self.scraping_funcs.page_is_listing(soup_html):
            return PageType.LISTING
        elif self.scraping_funcs.page_is_seller(soup_html):
            return PageType.SELLER
        elif self.scraping_funcs.page_is_search_result(soup_html):
            return PageType.SEARCH_RESULT
        elif self.scraping_funcs.page_is_login_page(soup_html):
            return PageType.LOGIN_PAGE
        elif self.scraping_funcs.page_is_ddos_protection(soup_html):
            return PageType.ANTI_DDOS
        elif self.scraping_funcs.page_is_main_page(soup_html):
            return PageType.CATEGORY_INDEX
        elif self.scraping_funcs.page_is_not_found_error(soup_html):
            return PageType.ERROR
        else:
            a = 0
            # raise AssertionError("Unknown page type.")

    def _get_seller(self, seller_name: str) -> Tuple[Optional[Seller], bool]:

        with self.__current_tasks_lock__:
            existing_seller = self.db_session.query(Seller) \
                .filter_by(name=seller_name, market=self.market_id).first()

            if existing_seller:
                seller = existing_seller
                return seller, False
            else:
                seller = Seller(name=seller_name, market=self.market_id)
                self.db_session.add(seller)
                self.db_session.commit()
                return seller, True
