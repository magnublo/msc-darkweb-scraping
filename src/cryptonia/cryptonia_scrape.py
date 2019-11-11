from multiprocessing import Queue
from random import shuffle
from threading import RLock
from typing import Tuple, Type

import cfscrape
import requests
from bs4 import BeautifulSoup
from requests import Response

from definitions import CRYPTONIA_MARKET_CATEGORY_INDEX_URL_PATH, CRYPTONIA_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE, \
    CRYPTONIA_MARKET_LOGIN_PHRASE, \
    CRYPTONIA_SRC_DIR, CRYPTONIA_MARKET_ID, CRYPTONIA_MARKET_SUCCESSFUL_LOGIN_PHRASE, \
    CRYPTONIA_MIN_CREDENTIALS_PER_THREAD
from src.base.base_functions import BaseFunctions
from src.base.base_scraper import BaseScraper
from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions, \
    CryptoniaScrapingFunctions
from src.db_utils import get_column_name
from src.models.feedback import Feedback
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.verified_external_account import VerifiedExternalAccount
from src.utils import get_page_as_soup_html


def _unit_types_are_equal(unit_type: str, second_unit_type: str) -> bool:
    shortest_string_length = min(len(unit_type), len(second_unit_type))

    return unit_type[0:shortest_string_length] == second_unit_type[0:shortest_string_length]


class CryptoniaScrapingSession(BaseScraper):



    __refresh_mirror_db_lock__ = RLock()
    __user_credentials_db_lock__ = RLock()
    __mirror_failure_lock__ = RLock()

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int, proxy: dict, session_id: int):
        super().__init__(queue, nr_of_threads, thread_id=thread_id, proxy=proxy, session_id=session_id)

    def _get_mirror_failure_lock(self) -> RLock:
        return self._get_mirror_failure_lock()

    def _get_min_credentials_per_thread(self) -> int:
        return CRYPTONIA_MIN_CREDENTIALS_PER_THREAD

    def _get_mirror_db_lock(self) -> RLock:
        return self.__refresh_mirror_db_lock__

    def _get_user_credentials_db_lock(self) -> RLock:
        return self.__user_credentials_db_lock__

    def _get_web_session_object(self) -> requests.Session:
        return cfscrape.Session()

    def populate_queue(self) -> None:
        self.logger.info(f"Fetching {self.mirror_base_url}{CRYPTONIA_MARKET_CATEGORY_INDEX_URL_PATH}")
        web_response = self._get_logged_in_web_response(CRYPTONIA_MARKET_CATEGORY_INDEX_URL_PATH)
        soup_html = get_page_as_soup_html(web_response.text)
        listing_category_pairs, category_base_urls = \
            scrapingFunctions.get_category_pairs_and_urls(soup_html)
        task_list = []

        for listing_category_pair, category_base_url in zip(listing_category_pairs, category_base_urls):
            self.logger.info(f"Fetching {self.mirror_base_url}{category_base_url}...")
            web_response = self._get_logged_in_web_response(category_base_url)
            soup_html = get_page_as_soup_html(web_response.text)
            nr_of_pages = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
            if nr_of_pages is not 0:
                task_list.append((listing_category_pair, category_base_url))
            for k in range(1, nr_of_pages):
                task_list.append((listing_category_pair, f"{category_base_url}/{k+1}"))

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def _scrape_queue_item(self, category_pair: Tuple[Tuple[str, int, str, int]],
                           search_result_url: str) -> None:
        web_response = self._get_logged_in_web_response(search_result_url)

        soup_html = get_page_as_soup_html(web_response.text)

        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)

        if len(product_page_urls) == 0:
            if soup_html.text.find(CRYPTONIA_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE) == -1:
                raise AssertionError  # raise error if no logical reason why search result is empty
            else:
                return

        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)

        assert len(titles) == len(sellers) == len(seller_urls) == len(product_page_urls)

        for title, seller_name, seller_url, product_page_url in zip(titles, sellers, seller_urls,
                                                                    product_page_urls):
            self._db_error_catch_wrapper(self.db_session, title, seller_name, seller_url, product_page_url,
                                         btc_rate, xmr_rate, category_pair, func=self._scrape_listing)

    def _scrape_listing(self, title: str, seller_name: str, seller_url: str, product_page_url: str, btc_rate: float,
                        xmr_rate: float, category_pair: Tuple[Tuple[str, int, str, int]]):
        seller, is_new_seller = self._get_seller(seller_name)

        listing_observation, is_new_listing_observation = self._get_listing_observation(title, seller.id)

        if not is_new_listing_observation:
            return

        is_new_seller_observation = self._exists_seller_observation_from_this_session(seller.id)

        if is_new_seller_observation:
            self._scrape_seller(seller_url, seller, is_new_seller)

        self.print_crawling_debug_message(url=product_page_url)

        web_response = self._get_logged_in_web_response(product_page_url)
        soup_html = get_page_as_soup_html(web_response.text)

        listing_type = scrapingFunctions.get_listing_type(soup_html)

        listing_text = scrapingFunctions.get_description(soup_html)

        accepts_BTC, accepts_BTC_multisig, accepts_XMR = scrapingFunctions.accepts_currencies(soup_html)
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)
        quantity_in_stock, second_unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)

        if not _unit_types_are_equal(unit_type, second_unit_type):
            raise AssertionError("Unit types are not consistent across listing.")

        origin_country: str
        destination_countries: Tuple[str]
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)
        escrow = scrapingFunctions.supports_escrow(soup_html)

        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)

        bulk_prices = scrapingFunctions.get_bulk_prices(soup_html)

        self._add_shipping_methods(listing_observation.id, shipping_methods)

        self._add_bulk_prices(listing_observation.id, bulk_prices)

        self._add_category_junctions(listing_observation.id, category_pair)

        listing_text_id: int = self._add_text(listing_text)

        country_ids: Tuple[int] = self._add_countries(origin_country, *destination_countries)
        destination_country_ids = country_ids[1:]
        self._add_country_junctions(destination_country_ids, listing_observation.id)

        listing_observation.listing_text_id = listing_text_id
        listing_observation.btc = accepts_BTC
        listing_observation.btc_multisig = accepts_BTC_multisig
        listing_observation.xmr = accepts_XMR
        listing_observation.url = product_page_url
        listing_observation.btc_rate = btc_rate
        listing_observation.xmr_rate = xmr_rate
        listing_observation.fiat_currency = fiat_currency
        listing_observation.price = price
        listing_observation.origin_country = country_ids[0]
        listing_observation.escrow = escrow
        listing_observation.quantity_in_stock = quantity_in_stock
        listing_observation.unit_type = unit_type
        listing_observation.minimum_order_unit_amount = minimum_order_unit_amount
        listing_observation.listing_type = listing_type

        self.db_session.flush()

    def _scrape_seller(self, seller_url, seller, is_new_seller):
        self.print_crawling_debug_message(url=seller_url)

        web_response = self._get_logged_in_web_response(seller_url)
        soup_html = get_page_as_soup_html(web_response.text)

        description = scrapingFunctions.get_seller_about_description(soup_html)

        percent_positive_rating, (disputes_won, disputes_lost), external_market_verifications, (
            cryptocurrency_unit_on_escrow, cryptocurrency_amount_on_escrow, fiat_unit_on_escrow,
            fiat_amount_on_escrow), ships_from, ships_to, \
        xmpp_jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        description_text_hash = self._add_text(description)
        self._scrape_feedback(seller, is_new_seller, soup_html=soup_html)

        pgp_key_content = scrapingFunctions.get_pgp_key(soup_html)
        self._add_pgp_key(seller, pgp_key_content)
        terms_and_conditions_text: str = scrapingFunctions.get_terms_and_conditions(soup_html)
        terms_and_conditions_id: int = self._add_text(terms_and_conditions_text)

        seller_observation = SellerObservation(
            seller_id=seller.id,
            session_id=self.session_id,
            description=description_text_hash,
            terms_and_conditions_id=terms_and_conditions_id,
            url=seller_url,
            disputes=disputes_won + disputes_lost,
            last_online=last_online,
            parenthesis_number=parenthesis_number,
            positive_feedback_received_percent=percent_positive_rating,
            vendor_level=vendor_level,
            disputes_won=disputes_won,
            disputes_lost=disputes_lost,
            cryptocurrency_unit_on_escrow=cryptocurrency_unit_on_escrow,
            cryptocurrency_amount_on_escrow=cryptocurrency_amount_on_escrow,
            fiat_unit_on_escrow=fiat_unit_on_escrow,
            fiat_amount_on_escrow=fiat_amount_on_escrow,
            fe_enabled=fe_enabled,
            xmpp_jabber_id=xmpp_jabber_id
        )

        if is_new_seller:
            self.db_session.add(seller)
            seller.registration_date = member_since

        self.db_session.add(seller_observation)
        self.db_session.flush()

        self._add_external_market_verifications(seller_observation_id=seller_observation.id,
                                                external_market_verifications=external_market_verifications)

    def _get_market_id(self) -> str:
        return CRYPTONIA_MARKET_ID

    def _get_working_dir(self) -> str:
        return CRYPTONIA_SRC_DIR

    def _get_headers(self) -> dict:
        return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": '1',
                "Cache-Control": "max-age=0}"
                }

    def _has_successful_login_phrase(self) -> bool:
        return True

    def _get_successful_login_phrase(self) -> str:
        return CRYPTONIA_MARKET_SUCCESSFUL_LOGIN_PHRASE

    def _get_login_url(self) -> str:
        return "/login"

    def _get_is_logged_out_phrase(self) -> str:
        return CRYPTONIA_MARKET_LOGIN_PHRASE

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        return CryptoniaScrapingFunctions

    def _get_anti_captcha_kwargs(self):
        return {
            'numeric': 2,
            'case': True
        }

    def _scrape_feedback(self, seller: Seller, is_new_seller: bool, soup_html: BeautifulSoup = None, url: str = None):

        if url:
            self.print_crawling_debug_message(url=url)
            web_response = self._get_logged_in_web_response(url)
            soup_html = get_page_as_soup_html(web_response.text)

        feedback_array = scrapingFunctions.get_feedbacks(soup_html)

        for publication_date, feedback_category, title, feedback_message_text, text_hash, buyer, crypto_currency, \
            price in list(
                zip(*feedback_array)):
            if not is_new_seller:
                existing_feedback = self.db_session.query(Feedback).filter_by(
                    date_published=publication_date,
                    buyer=buyer,
                    category=feedback_category,
                    text_hash=text_hash,
                    currency=crypto_currency,
                    market=self.market_id) \
                    .join(Seller, Seller.id == Feedback.seller_id) \
                    .first()

                if existing_feedback:
                    self.db_session.flush()
                    return

            db_feedback = Feedback(
                date_published=publication_date,
                category=feedback_category,
                market=self.market_id,
                seller_id=seller.id,
                session_id=self.session_id,
                product_title=title,
                feedback_message_text=feedback_message_text,
                text_hash=text_hash,
                buyer=buyer,
                currency=crypto_currency,
                price=price
            )
            self.db_session.add(db_feedback)

        self.db_session.flush()

        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)

        if next_feedback_url:
            self._scrape_feedback(seller, is_new_seller, url=next_feedback_url)

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
            self.db_session.flush()

    @staticmethod
    def _is_successful_login_response(response: Response) -> bool:
        return response.text.find(CRYPTONIA_MARKET_SUCCESSFUL_LOGIN_PHRASE) != -1

    def _login_and_set_cookie(self, web_session: requests.Session, web_response: Response):
        web_session.cookies.clear()
        super()._login_and_set_cookie(web_session, web_response)
