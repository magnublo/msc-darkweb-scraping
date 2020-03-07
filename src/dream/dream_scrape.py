import datetime
import hashlib
import os
import pickle
import re
from multiprocessing.queues import Queue
from threading import Lock
from time import time
from typing import Type, Dict, Tuple, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests import Response

from definitions import DREAM_MARKET_ID, DREAM_SRC_DIR, MD5_HASH_STRING_ENCODING, FEEDBACK_TEXT_HASH_COLUMN_LENGTH
from src.base.base_functions import BaseFunctions
from src.base.base_logger import BaseClassWithLogger
from src.base.base_scraper import BaseScraper
from src.db_utils import get_engine, get_db_session
from src.dream.dream_functions import DreamScrapingFunctions
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.verified_external_account import VerifiedExternalAccount
from src.utils import PageType, get_page_as_soup_html


def get_usd_price_from_rates(price: float, currency: str, fiat_exchange_rates: Dict[str, float]) -> float:
    if currency == "USD":
        return price
    else:
        btc_price = price / fiat_exchange_rates[currency]
        return btc_price * fiat_exchange_rates["USD"]


def get_crypto_to_usd_rates(fiat_exchange_rates: Dict[str, float]) -> Tuple[float, float, float]:
    # btc_rate, bch_rate, xmr_rate
    btc_rate = fiat_exchange_rates["USD"]
    bch_rate = btc_rate / fiat_exchange_rates["BCH"]
    xmr_rate = btc_rate / fiat_exchange_rates["XMR"]
    return btc_rate, bch_rate, xmr_rate


def process_shipping_methods(unprocessed_shipping_methods: Tuple[Tuple[str, None, str, float, None, None]],
                             fiat_exchange_rates: Dict[str, float]) -> Tuple[Tuple[str, None, str, float, None, None]]:
    shipping_methods: List[Tuple[str, None, str, float, None, None]] = []
    for description, _, currency, price, _, _ in unprocessed_shipping_methods:
        usd_price = get_usd_price_from_rates(price, currency, fiat_exchange_rates)
        shipping_methods.append((description, None, "USD", usd_price, None, None))

    return tuple(shipping_methods)


class PageMetadata:

    def __init__(self, meta_data_dict: Dict):

        self.created_date: datetime = meta_data_dict["meta"]["received_on"]
        self.url: str = self.process_url(meta_data_dict["url"])

    @staticmethod
    def process_url(unprocessed_url: str) -> str:
        # http://7ep7acrkunzdcw3l.onion/./viewProduct?offer=101998.516894
        urlparse_obj = urlparse(unprocessed_url)
        unprocessed_url_path = urlparse_obj.path
        match = re.search(r"(?:\/\.\/)*(.+)$", unprocessed_url_path)
        if match:
            start_index = match.regs[1][0]
            end_index = match.regs[1][1]
            url_path = unprocessed_url_path[start_index:end_index]
        else:
            url_path = unprocessed_url_path
        return "/" + url_path + "?" + urlparse_obj.query


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
            self._scrape_listing(soup_html, meta_data.created_date, meta_data.url)
            pass
        elif page_type == PageType.SELLER:
            self._scrape_seller(soup_html, meta_data.created_date, meta_data.url)
            pass

    def _scrape_listing(self, soup_html: BeautifulSoup, created_date: datetime, url: str) -> None:
        seller: Seller
        is_new_seller: bool
        listing_observation: ListingObservation
        is_new_listing_observation: bool
        is_new_seller_observation: bool
        web_response: requests.Response
        soup_html: BeautifulSoup
        listing_text: str
        listing_categories: Tuple[Tuple[str, int, Optional[str], Optional[int]], ...]
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
        seller, _ = self._fetch_seller(seller_name)
        title = self.scraping_funcs.get_listing_title(soup_html)
        listing_categories = self.scraping_funcs.get_categories(soup_html)

        fiat_exchange_rates: Dict[str, float] = self.scraping_funcs.get_fiat_exchange_rates(soup_html)
        price, currency = self.scraping_funcs.get_price_and_currency(soup_html)
        fiat_price = get_usd_price_from_rates(price, currency, fiat_exchange_rates)
        btc_rate, bch_rate, xmr_rate = get_crypto_to_usd_rates(fiat_exchange_rates)

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
        country_ids: Tuple[int] = self._add_countries(origin_country, *destination_countries)
        origin_country_id = country_ids[0]

        # noinspection PyTypeChecker
        listing_observation = ListingObservation(thread_id=self.thread_id, created_date=created_date,
                                                 session_id=self.session_id, listing_text_id=listing_text_id,
                                                 title=title, url=url, btc=accepts_BTC, xmr=accepts_XMR,
                                                 btc_multisig=accepts_BTC_multisig,
                                                 seller_id=seller.id, price=fiat_price, fiat_currency=fiat_currency,
                                                 origin_country=origin_country_id, btc_rate=btc_rate, xmr_rate=xmr_rate,
                                                 escrow=escrow, listing_type=None, quantity_in_stock=None,
                                                 promoted_listing=None, ltc=False, ltc_rate=None, nr_sold=None,
                                                 nr_sold_since_date=None, ends_in=None, nr_of_views=None,
                                                 minimum_order_unit_amount=None, unit_type=None, bch=accepts_BCH,
                                                 bch_rate=bch_rate, fifty_percent_finalize_early=None)

        self.db_session.add(ListingObservation)
        self.db_session.commit()

        self._add_shipping_methods(listing_observation.id, shipping_methods)
        self._add_category_junctions(listing_observation.id, listing_categories)
        destination_country_ids = country_ids[1:]
        self._add_country_junctions(destination_country_ids, listing_observation.id)

        self.db_session.commit()

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

    def _fetch_seller(self, seller_name: str) -> Tuple[Optional[Seller], bool]:

        existing_seller = self.db_session.query(Seller) \
            .filter_by(name=seller_name, market=self.market_id).first()

        assert existing_seller is not None

        return existing_seller, False

    def _scrape_seller(self, soup_html: BeautifulSoup, created_date: datetime, url: str):
        self.scraping_funcs: DreamScrapingFunctions

        seller_name = self.scraping_funcs.get_seller_name(soup_html)
        seller, is_new_seller = self._get_seller(seller_name)
        terms_and_conditions_text: str = self.scraping_funcs.get_terms_and_conditions(soup_html)
        terms_and_conditions_id: int = self._add_text(terms_and_conditions_text)
        pgp_key_content = self.scraping_funcs.get_pgp_key(soup_html)
        nr_of_sales, rating = self.scraping_funcs.get_number_of_sales_and_rating(soup_html)
        positive_percent_received_feedback = (rating / 5) * 100
        fe_enabled = self.scraping_funcs.get_fe_enabled(soup_html)

        disputes, orders, spendings, feedback_left, \
        feedback_percent_positive, description, positive_1m, positive_6m, positive_12m, \
        neutral_1m, neutral_6m, neutral_12m, \
        negative_1m, negative_6m, negative_12m, stealth_rating, quality_rating, value_price_rating, vendor_level, \
        trust_level, disputes_won, disputes_lost, cryptocurrency_amount_on_escrow, fiat_amount_on_escrow, \
        fiat_unit_on_escrow, cryptocurrency_unit_on_escrow, xmpp_jabber_id, \
        email, autofinalized_orders = [None] * 29

        is_banned = False

        last_online: datetime = self.scraping_funcs.get_last_online(soup_html)
        registration_date: datetime = self.scraping_funcs.get_registration_date(soup_html)

        external_market_verifications: Tuple[
            Tuple[str, int, float, float, int, int, int, str]] = self.scraping_funcs.get_external_market_ratings(
            soup_html)

        self._scrape_feedback(seller, created_date)

        seller_observation = SellerObservation(created_date=created_date, session_id=self.session_id, url=url,
                                               seller_id=seller.id, description=description,
                                               terms_and_conditions_id=terms_and_conditions_id, disputes=disputes,
                                               last_online=last_online, parenthesis_number=nr_of_sales,
                                               positive_feedback_received_percent=positive_percent_received_feedback,
                                               vendor_level=vendor_level, orders=orders, spendings=spendings,
                                               feedback_left=feedback_left,
                                               feedback_percent_positive=feedback_percent_positive,
                                               stealth_rating=stealth_rating, quality_rating=quality_rating,
                                               value_price_rating=value_price_rating, trust_level=trust_level,
                                               positive_1m=positive_1m, positive_6m=positive_6m,
                                               positive_12m=positive_12m, neutral_1m=neutral_1m, neutral_6m=neutral_6m,
                                               neutral_12m=neutral_12m, negative_1m=negative_1m,
                                               negative_6m=negative_6m, negative_12m=negative_12m, banned=is_banned,
                                               disputes_won=disputes_won, disputes_lost=disputes_lost,
                                               cryptocurrency_amount_on_escrow=cryptocurrency_amount_on_escrow,
                                               fiat_amount_on_escrow=fiat_amount_on_escrow,
                                               cryptocurrency_unit_on_escrow=cryptocurrency_unit_on_escrow,
                                               fiat_unit_on_escrow=fiat_unit_on_escrow, fe_enabled=fe_enabled,
                                               xmpp_jabber_id=xmpp_jabber_id, email=email,
                                               autofinalized_orders=autofinalized_orders)

        self._add_pgp_key(seller, pgp_key_content)
        self._add_external_market_verifications(seller_observation.id, external_market_verifications)

        if is_new_seller:
            seller.registration_date = registration_date

        self.db_session.add(seller_observation)
        self.db_session.commit()

    def _add_external_market_verifications(self, seller_observation_id: int, external_market_verifications: Tuple[
        Tuple[str, int, float, float, int, int, int, str]]) -> None:

        for market_id, sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text in \
                external_market_verifications:
            self.db_session.add(
                VerifiedExternalAccount(
                    seller_observation_id=seller_observation_id, market_id=market_id,
                    confirmed_sales=sales, rating=rating, max_rating=max_rating, nr_of_good_reviews=good_reviews,
                    nr_of_neutral_reviews=neutral_reviews, nr_of_bad_reviews=bad_reviews, free_text=free_text)
            )
            self.db_session.commit()

    def _scrape_feedback(self, soup_html: BeautifulSoup, seller: Seller, created_date: datetime) -> None:
        self.scraping_funcs: DreamScrapingFunctions
        feedback_rows: Tuple[BeautifulSoup] = soup_html.select_one(
            "body > div.main.onlyLeftNavLayout > div.content > div > div:nth-child(6) > table > tbody > tr")

        if not feedback_rows:
            return

        earlier_feedback = self.db_session.query(Feedback).filter(Feedback.seller_id == seller.id).all()
        fiat_exchange_rate_dict: Dict[str, float] = self.scraping_funcs.get_fiat_exchange_rates_from_seller_page(soup_html)

        for feedback_row in feedback_rows:
            time_ago_td, star_td, message_text_td, buyer_name_td, price_td = feedback_row.select("td")
            date_published: datetime = created_date - get_timedelta_from_str(time_ago_td.text.strip())
            star_rating: int = len([img for img in star_td.select("img") if img["src"].find("star_gold") != -1])
            message_text = message_text_td.text.strip()
            message_text_hash = hashlib.md5(
                message_text.encode(MD5_HASH_STRING_ENCODING)
            ).hexdigest()[:FEEDBACK_TEXT_HASH_COLUMN_LENGTH]
            buyer = buyer_name_td.text.strip()