import hashlib
from datetime import datetime
from math import ceil
from multiprocessing import Queue
from random import shuffle
from threading import Lock
from typing import List, Tuple, Type, Optional

import requests
from bs4 import BeautifulSoup
from requests import Response

from definitions import EMPIRE_MARKET_ID, EMPIRE_SRC_DIR, \
    EMPIRE_HTTP_HEADERS, \
    FEEDBACK_TEXT_HASH_COLUMN_LENGTH, EMPIRE_MARKET_LOGIN_PHRASE, \
    EMPIRE_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE, MD5_HASH_STRING_ENCODING, EMPIRE_MARKET_CATEGORY_INDEX_URL_PATH, \
    EMPIRE_MIN_CREDENTIALS_PER_THREAD
from src.base.base_functions import BaseFunctions
from src.base.base_scraper import BaseScraper
from src.db_utils import get_column_name
from src.empire.empire_functions import EmpireScrapingFunctions
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.verified_external_account import VerifiedExternalAccount
from src.utils import get_page_as_soup_html, get_standardized_listing_type, ListingType


def _parse_payment_type(payment_type: str) -> Tuple[bool, bool]:
    # accepts multisig, has escrow
    if payment_type.lower() == "Escrow".lower():
        return False, True
    elif payment_type.lower() == "Escrow, MultiSig".lower():
        return True, True
    elif payment_type.lower() == "FE Listing 100%".lower():
        return False, False
    else:
        raise AssertionError('Unknown listing field content in "Payment".')


def _get_final_quantity_in_stock(first_quantity_in_stock: Optional[int], second_quantity_in_stock: Optional[int]) -> \
        Optional[int]:
    # both are None
    if first_quantity_in_stock is None and second_quantity_in_stock is None:
        return None

    # return lowest of those quantities which are not None
    return min([i for i in [first_quantity_in_stock, second_quantity_in_stock] if i is not None])


def _is_redirect_to_home(mirror_base_url: str, web_response: requests.Response) -> bool:
    for history_response in web_response.history:
        if history_response.is_redirect:
            if history_response.headers.get('location') == f"{mirror_base_url}{EMPIRE_MARKET_CATEGORY_INDEX_URL_PATH}":
                return True
    return False


class EmpireScrapingSession(BaseScraper):
    __mirror_manager_lock__ = Lock()
    __user_credentials_db_lock__ = Lock()
    __mirror_failure_lock__ = Lock()

    def _get_anti_captcha_kwargs(self) -> dict:
        return {
                'numeric': 1,
                'comment': 'BLACK numbers only'
                }

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int, proxy: dict,
                 session_id: int):
        super().__init__(queue, nr_of_threads, thread_id=thread_id, proxy=proxy,
                         session_id=session_id)

    def _is_logged_out(self, web_session: requests.Session, response: Response, login_url: str,
                       login_page_phrase: str) -> bool:

        soup_html = get_page_as_soup_html(response.text)

        if self.scraping_funcs.is_logged_in(soup_html, web_session.username):
            return False

        body = soup_html.select_one("body")
        if body and body.text == "404 error":
            # This page is served both when user is successfully logged in, and when user tries to access
            # logged in resource when logged out. This case warrants an extra web request to verify logged-in-logged-out
            # status.
            self.logger.info(f"Got 404. Ambiguous authorization state. Retrieving {self._get_login_url()}...")
            web_response = self._get_web_response_with_error_catch(web_session, 'GET', '/',
                                                                   headers=self.headers, proxies=self.proxy)
            return self._is_logged_out(web_session, web_response, login_url, login_page_phrase)

        return True

    def _handle_custom_server_error(self) -> None:
        raise NotImplementedError('')

    def _is_custom_server_error(self, response) -> bool:
        return False

    def _get_mirror_failure_lock(self) -> Lock:
        return self.__mirror_failure_lock__

    def _get_successful_login_phrase(self) -> str:
        return ""

    def _get_min_credentials_per_thread(self) -> int:
        return EMPIRE_MIN_CREDENTIALS_PER_THREAD

    def _get_mirror_db_lock(self) -> Lock:
        return self.__mirror_manager_lock__

    def _get_user_credentials_db_lock(self) -> Lock:
        return self.__user_credentials_db_lock__

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        return EmpireScrapingFunctions

    def _get_web_session_object(self) -> requests.Session:
        return requests.Session()

    def _get_working_dir(self) -> str:
        return EMPIRE_SRC_DIR

    def _get_login_url(self) -> str:
        return "/index/login"

    def _get_home_url(self) -> str:
        return "/home"

    def _get_is_logged_out_phrase(self) -> str:
        return EMPIRE_MARKET_LOGIN_PHRASE

    def _get_market_id(self) -> str:
        return EMPIRE_MARKET_ID

    def _get_headers(self) -> dict:
        headers = EMPIRE_HTTP_HEADERS
        if self.mirror_base_url:
            headers["Referer"] = self._get_schemaed_url_from_path("/login")
            headers["Host"] = self.mirror_base_url
        return headers

    def populate_queue(self):
        self.logger.info(f"Fetching {EMPIRE_MARKET_CATEGORY_INDEX_URL_PATH} and creating task queue...")
        web_response = self._get_logged_in_web_response(EMPIRE_MARKET_CATEGORY_INDEX_URL_PATH)
        soup_html = get_page_as_soup_html(web_response.text)
        pairs_of_category_base_urls_and_nr_of_listings = self.scraping_funcs.get_category_urls_and_nr_of_listings(
            soup_html)
        task_list = []

        for i in range(0, len(pairs_of_category_base_urls_and_nr_of_listings)):
            nr_of_listings = int(pairs_of_category_base_urls_and_nr_of_listings[i][1])
            url = pairs_of_category_base_urls_and_nr_of_listings[i][0]
            nr_of_pages = ceil(nr_of_listings / 15)
            for k in range(0, nr_of_pages):
                task_list.append((url + str(k * 15),))

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.logger.info(f"Queue has been populated with {len(task_list)} tasks.")
        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def _scrape_listing(self, title: str, seller_name: str, seller_url: str, product_page_url: str, is_sticky: bool,
                        nr_of_views: int, btc_rate: float, ltc_rate: float, xmr_rate: float):
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
        nr_sold: int
        nr_sold_since_date: datetime
        fiat_currency: str
        price: float
        origin_country: str
        destination_countries: Tuple[str]
        payment_type: str
        accepts_BTC_multisig: bool
        escrow: bool
        non_standardized_listing_type: str
        first_quantity_in_stock: int
        second_quantity_in_stock: int
        ends_in: str
        is_auto_dispatch: bool
        self.scraping_funcs: EmpireScrapingFunctions
        shipping_methods: Tuple[Tuple[str, int, str, float, Optional[str], bool]]

        seller, is_new_seller = self._get_seller(seller_name)

        listing_observation, is_new_listing_observation = self._get_listing_observation(title, seller.id)

        if not is_new_listing_observation:
            if listing_observation.promoted_listing != is_sticky:
                listing_observation.promoted_listing = True
                self.db_session.flush()
            return

        is_new_seller_observation = self._exists_seller_observation_from_this_session(seller.id)

        if is_new_seller_observation:
            self._scrape_seller(seller_url, seller, is_new_seller)

        self.print_crawling_debug_message(url=product_page_url)

        web_response = self._get_logged_in_web_response(product_page_url)
        soup_html = get_page_as_soup_html(web_response.text)

        try:
            listing_text = self.scraping_funcs.get_description(soup_html)
        except AssertionError as e:
            if _is_redirect_to_home(self.mirror_base_url, web_response):
                return
            else:
                raise e

        listing_categories = self.scraping_funcs.get_listing_categories(soup_html)
        accepts_BTC, accepts_LTC, accepts_XMR = self.scraping_funcs.accepts_currencies(soup_html)
        nr_sold, nr_sold_since_date = self.scraping_funcs.get_nr_sold_since_date(soup_html)
        fiat_currency, price = self.scraping_funcs.get_fiat_currency_and_price(soup_html)
        origin_country, destination_countries, payment_type = \
            self.scraping_funcs.get_origin_country_and_destinations_and_payment_type(
                soup_html)

        accepts_BTC_multisig, escrow = _parse_payment_type(payment_type)

        non_standardized_listing_type, first_quantity_in_stock, ends_in = \
            self.scraping_funcs.get_product_class_quantity_left_and_ends_in(
                soup_html)

        is_auto_dispatch, second_quantity_in_stock = self.scraping_funcs.has_unlimited_dispatch_and_quantity_in_stock(
            soup_html)
        final_quantity_in_stock: int = _get_final_quantity_in_stock(first_quantity_in_stock, second_quantity_in_stock)

        standardized_listing_type: str = get_standardized_listing_type(non_standardized_listing_type)
        if is_auto_dispatch and standardized_listing_type == ListingType.MANUAL_DIGITAL.name:
            standardized_listing_type = ListingType.AUTO_DIGITAL.name

        shipping_methods = self.scraping_funcs.get_shipping_methods(soup_html)
        bulk_prices = self.scraping_funcs.get_bulk_prices(soup_html)

        self._add_bulk_prices(listing_observation.id, bulk_prices)
        self._add_shipping_methods(listing_observation.id, shipping_methods)
        self._add_category_junctions(listing_observation.id, listing_categories)

        listing_text_id: int = self._add_text(listing_text)

        country_ids: Tuple[int] = self._add_countries(origin_country, *destination_countries)
        destination_country_ids = country_ids[1:]
        self._add_country_junctions(destination_country_ids, listing_observation.id)

        listing_observation.listing_text_id = listing_text_id
        listing_observation.btc = accepts_BTC
        listing_observation.ltc = accepts_LTC
        listing_observation.xmr = accepts_XMR
        listing_observation.btc_multisig = accepts_BTC_multisig
        listing_observation.nr_sold = nr_sold
        listing_observation.nr_sold_since_date = nr_sold_since_date
        listing_observation.promoted_listing = is_sticky
        listing_observation.url = product_page_url
        listing_observation.btc_rate = btc_rate
        listing_observation.ltc_rate = ltc_rate
        listing_observation.xmr_rate = xmr_rate
        listing_observation.fiat_currency = fiat_currency
        listing_observation.price = price
        listing_observation.origin_country = country_ids[0]
        listing_observation.escrow = escrow
        listing_observation.listing_type = standardized_listing_type
        listing_observation.quantity_in_stock = final_quantity_in_stock
        listing_observation.ends_in = ends_in
        listing_observation.nr_of_views = nr_of_views

        self.db_session.flush()

    def _scrape_seller(self, seller_url, seller, is_new_seller):
        self.print_crawling_debug_message(url=seller_url)

        web_response = self._get_logged_in_web_response(seller_url)
        soup_html = get_page_as_soup_html(web_response.text)

        seller_name = seller.name
        description = self.scraping_funcs.get_seller_about_description(soup_html, seller_name)

        disputes, orders, spendings, feedback_left, \
        feedback_percent_positive, last_online = self.scraping_funcs.get_buyer_statistics(soup_html)

        positive_1m, positive_6m, positive_12m, \
        neutral_1m, neutral_6m, neutral_12m, \
        negative_1m, negative_6m, negative_12m = self.scraping_funcs.get_seller_statistics(soup_html)

        stealth_rating, quality_rating, value_price_rating = self.scraping_funcs.get_star_ratings(soup_html)
        is_banned: bool = self.scraping_funcs.user_is_banned(soup_html)

        parenthesis_number, vendor_level, trust_level = \
            self.scraping_funcs.get_parenthesis_number_and_vendor_and_trust_level(
                soup_html)

        positive_feedback_received_percent, registration_date = self.scraping_funcs.get_mid_user_info(soup_html)

        external_market_verifications: Tuple[
            Tuple[str, int, float, str]] = self.scraping_funcs.get_external_market_ratings(
            soup_html)

        seller_observation_description = self._add_text(description)

        previous_seller_observation = self.db_session.query(
            SellerObservation).join(Seller, SellerObservation.seller_id == Seller.id, isouter=False).filter(
            Seller.id == seller.id,
            Seller.market == self.market_id
        ).order_by(SellerObservation.created_date.desc()).first()

        if previous_seller_observation:
            new_positive_feedback = previous_seller_observation.positive_1m < positive_1m
            new_neutral_feedback = previous_seller_observation.neutral_1m < neutral_1m
            new_negative_feedback = previous_seller_observation.negative_1m < negative_1m
            new_left_feedback = previous_seller_observation.feedback_left < feedback_left
            category_contains_new_feedback = [new_positive_feedback, new_neutral_feedback, new_negative_feedback,
                                              new_left_feedback]
        else:
            category_contains_new_feedback = [True, True, True, True]

        feedback_categories, feedback_urls, pgp_url = \
            self.scraping_funcs.get_feedback_categories_and_feedback_urls_and_pgp_url(
                soup_html)

        assert len(feedback_urls) == len(feedback_categories) == len(category_contains_new_feedback)

        for i in range(0, len(feedback_categories)):
            if category_contains_new_feedback[i]:
                self._scrape_feedback(seller, is_new_seller, feedback_categories[i], feedback_urls[i])

        self._scrape_pgp_key(seller, is_new_seller, pgp_url)

        seller_observation = SellerObservation(
            seller_id=seller.id,
            session_id=self.session_id,
            description=seller_observation_description,
            url=seller_url,
            disputes=disputes,
            orders=orders,
            spendings=spendings,
            feedback_left=feedback_left,
            feedback_percent_positive=feedback_percent_positive,
            last_online=last_online,
            parenthesis_number=parenthesis_number,
            positive_feedback_received_percent=positive_feedback_received_percent,
            positive_1m=positive_1m,
            positive_6m=positive_6m,
            positive_12m=positive_12m,
            neutral_1m=neutral_1m,
            neutral_6m=neutral_6m,
            neutral_12m=neutral_12m,
            negative_1m=negative_1m,
            negative_6m=negative_6m,
            negative_12m=negative_12m,
            stealth_rating=stealth_rating,
            quality_rating=quality_rating,
            value_price_rating=value_price_rating,
            vendor_level=vendor_level,
            trust_level=trust_level,
            banned=is_banned
        )

        if is_new_seller:
            seller.registration_date = registration_date

        self.db_session.add(seller_observation)
        self.db_session.flush()

        self._add_external_market_verifications(seller_observation.id, external_market_verifications)

    def _scrape_feedback(self, seller, is_new_seller, category, url):

        self.print_crawling_debug_message(url=url)

        web_response = self._get_logged_in_web_response(url)

        soup_html = get_page_as_soup_html(web_response.text)

        feedback_array = self.scraping_funcs.get_feedbacks(soup_html)

        for feedback in feedback_array:
            if not is_new_seller:
                existing_feedback = self.db_session.query(Feedback).filter_by(
                    date_published=feedback["date_published"],
                    buyer=feedback["buyer"],
                    category=category,
                    text_hash=hashlib.md5((feedback["feedback_message"] + feedback["seller_response_message"]).encode(
                        MD5_HASH_STRING_ENCODING)).hexdigest()[:FEEDBACK_TEXT_HASH_COLUMN_LENGTH],
                    market=self.market_id) \
                    .join(Seller, Seller.id == Feedback.seller_id) \
                    .first()

                if existing_feedback:
                    self.db_session.flush()
                    return

            db_feedback = Feedback(
                date_published=feedback["date_published"],
                category=category,
                market=self.market_id,
                seller_id=seller.id,
                session_id=self.session_id,
                product_url=feedback["product_url"],
                feedback_message_text=feedback["feedback_message"],
                seller_response_message=feedback["seller_response_message"],
                text_hash=hashlib.md5(
                    (feedback["feedback_message"] + feedback["seller_response_message"]).encode(
                        MD5_HASH_STRING_ENCODING)).hexdigest()[
                          :FEEDBACK_TEXT_HASH_COLUMN_LENGTH],
                buyer=feedback["buyer"],
                currency=feedback["currency"],
                price=feedback["price"]
            )
            self.db_session.add(db_feedback)

        self.db_session.flush()

        next_url_with_feeback = self.scraping_funcs.get_next_feedback_page(soup_html)

        if next_url_with_feeback:
            self._scrape_feedback(seller, is_new_seller, category, next_url_with_feeback)

    def _scrape_pgp_key(self, seller: Seller, is_new_seller: bool, url: str) -> None:

        scrape_pgp_this_session = self._should_scrape_pgp_key_this_session(seller, is_new_seller)

        if scrape_pgp_this_session:
            web_response = self._get_logged_in_web_response(url)
            soup_html = get_page_as_soup_html(web_response.text)
            pgp_key_content = self.scraping_funcs.get_pgp_key(soup_html)
            self._add_pgp_key(seller, pgp_key_content)

    def _scrape_queue_item(self, search_result_url: str):
        self.scraping_funcs: EmpireScrapingFunctions

        web_response = self._get_logged_in_web_response(search_result_url)
        if hasattr(web_response, 'do_continue'):
            return

        soup_html = get_page_as_soup_html(web_response.text)
        product_page_urls, urls_is_sticky, titles, sellers, seller_urls, nrs_of_views = \
            self.scraping_funcs.get_listing_infos(
                soup_html)

        if len(product_page_urls) == 0:
            if soup_html.text.find(EMPIRE_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE) == -1:
                raise AssertionError  # raise error if no logical reason why search result is empty
            else:
                return

        btc_rate, ltc_rate, xmr_rate = self.scraping_funcs.get_cryptocurrency_rates(soup_html)

        assert len(titles) == len(sellers) == len(seller_urls) == len(product_page_urls) == len(urls_is_sticky) == len(
            nrs_of_views)

        for title, seller_name, seller_url, product_page_url, is_sticky, nr_of_views in zip(titles, sellers,
                                                                                            seller_urls,
                                                                                            product_page_urls,
                                                                                            urls_is_sticky,
                                                                                            nrs_of_views):
            self._db_error_catch_wrapper(self.db_session, title, seller_name, seller_url, product_page_url,
                                         is_sticky, nr_of_views, btc_rate, ltc_rate, xmr_rate,
                                         func=self._scrape_listing)

    def _add_external_market_verifications(self, seller_observation_id: int,
                                           external_market_verifications: Tuple[Tuple[str, int, float, str]]) -> None:

        for market_id, sales, rating, free_text in external_market_verifications:
            self.db_session.add(
                VerifiedExternalAccount(
                    seller_observation_id=seller_observation_id, market_id=market_id,
                    confirmed_sales=sales, rating=rating, free_text=free_text)
            )
            self.db_session.flush()
