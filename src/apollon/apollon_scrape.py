import datetime
from random import shuffle
from threading import Lock
from typing import Type, Tuple, List, Optional

import requests
from bs4 import BeautifulSoup
from requests import Response
from sqlalchemy import func

from definitions import APOLLON_MARKET_ID, APOLLON_MARKET_GENERIC_CAPTCHA_INSTRUCTIONS, APOLLON_SRC_DIR, \
    APOLLON_HTTP_HEADERS, APOLLON_MIN_CREDENTIALS_PER_THREAD, APOLLON_MARKET_CATEGORY_INDEX_URL_PATH, \
    APOLLON_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE
from src.apollon.apollon_functions import ApollonScrapingFunctions
from src.base.base_functions import BaseFunctions
from src.base.base_scraper import BaseScraper
from src.db_utils import get_column_name
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.verified_external_account import VerifiedExternalAccount
from src.utils import PageType, get_page_as_soup_html, ListingType


class ApollonScrapingSession(BaseScraper):
    __mirror_manager_lock__ = Lock()
    __user_credentials_db_lock__ = Lock()
    __mirror_failure_lock__ = Lock()

    def _apply_processing_to_captcha_image(self, image_response, captcha_instruction):
        raise NotImplementedError('')

    def _captcha_instruction_is_generic(self, captcha_instruction: str) -> bool:
        return captcha_instruction in APOLLON_MARKET_GENERIC_CAPTCHA_INSTRUCTIONS

    def _is_expected_page(self, response: requests.Response, expected_page_type: PageType) -> bool:
        return True
        # LISTING = "listing",
        # SELLER = "seller",
        # FEEDBACK = "feedback",
        # PGP = "PGP key",
        # SEARCH_RESULT = "search result",
        # UNDEFINED = "arbitrary"

        # soup_html = get_page_as_soup_html(response.text)
        #
        # self.scraping_funcs: EmpireScrapingFunctions
        #
        # if expected_page_type == expected_page_type.LISTING:
        #     return self.scraping_funcs.is_listing(soup_html)
        # elif expected_page_type == expected_page_type.SELLER:
        #     return self.scraping_funcs.is_seller(soup_html)
        # elif expected_page_type == expected_page_type.FEEDBACK:
        #     return self.scraping_funcs.is_feedback(soup_html)
        # elif expected_page_type == expected_page_type.PGP:
        #     return self.scraping_funcs.is_pgp_key(soup_html)
        # elif expected_page_type == expected_page_type.SEARCH_RESULT:
        #     return self.scraping_funcs.is_search_result(soup_html)
        # elif expected_page_type == expected_page_type.CATEGORY_INDEX:
        #     return self.scraping_funcs.is_category_index(soup_html)
        # elif expected_page_type == expected_page_type.UNDEFINED:
        #     return True

    def _handle_custom_server_error(self) -> None:
        raise NotImplementedError('')

    def _get_captcha_image_request_headers(self, headers: dict) -> dict:
        new_headers = headers
        new_headers["Accept"] = "image/webp,image/apng,image/*,*/*;q=0.8"
        new_headers["Referer"] = f"{self.mirror_base_url}{self._get_login_url()}"
        return new_headers

    def _get_market_id(self) -> str:
        return APOLLON_MARKET_ID

    def _get_working_dir(self) -> str:
        return APOLLON_SRC_DIR

    def _get_headers(self) -> dict:
        return APOLLON_HTTP_HEADERS

    def _get_login_url(self) -> str:
        return "/login.php"

    def _get_is_logged_out_phrase(self) -> str:
        return ""

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        return ApollonScrapingFunctions

    def _get_anti_captcha_kwargs(self):
        return {
            'numeric': 0,
            'case': True,
            'comment': "ignore URL in bottom of image"
        }

    def _is_logged_out(self, web_session: requests.Session, response: Response, login_url: str,
                       login_page_phrase: str) -> bool:
        soup_html = get_page_as_soup_html(response.text)
        return not self.scraping_funcs.is_logged_in(soup_html, self.web_session.username)

    def _get_min_credentials_per_thread(self) -> int:
        return APOLLON_MIN_CREDENTIALS_PER_THREAD

    def _get_mirror_db_lock(self) -> Lock:
        return self.__mirror_manager_lock__

    def _get_user_credentials_db_lock(self) -> Lock:
        return self.__user_credentials_db_lock__

    def _get_mirror_failure_lock(self) -> Lock:
        return self.__mirror_failure_lock__

    def _is_custom_server_error(self, response) -> bool:
        return False

    def _get_web_session_object(self) -> requests.Session:
        return requests.session()

    def populate_queue(self) -> None:
        task_list: List[Tuple[any, str]] = []

        self.logger.info(f"Fetching {APOLLON_MARKET_CATEGORY_INDEX_URL_PATH} and creating task queue...")
        web_response = self._get_logged_in_web_response(APOLLON_MARKET_CATEGORY_INDEX_URL_PATH,
                                                        expected_page_type=PageType.CATEGORY_INDEX)
        soup_html = get_page_as_soup_html(web_response.text)

        self.scraping_funcs: ApollonScrapingFunctions

        main_category_index_urls, parent_sub_category_index_urls = \
            self.scraping_funcs.get_sub_categories_index_urls(
                soup_html)

        for parent_sub_category_index_url in parent_sub_category_index_urls:
            self.logger.info(f"Fetching {self.mirror_base_url}{parent_sub_category_index_url}...")
            web_response = self._get_logged_in_web_response(parent_sub_category_index_url)
            soup_html = get_page_as_soup_html(web_response.text)
            tasks = self.scraping_funcs.get_task_list_from_parent_sub_category_page(soup_html)
            for t in tasks:
                task_list.append(t)

        for main_category_index_url in main_category_index_urls:
            self.logger.info(f"Fetching {self.mirror_base_url}{main_category_index_url}...")
            web_response = self._get_logged_in_web_response(main_category_index_url)
            soup_html = get_page_as_soup_html(web_response.text)
            tasks = self.scraping_funcs.get_task_list_from_main_category_page(soup_html)
            for t in tasks:
                task_list.append(t)

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.logger.info(f"Queue has been populated with {len(task_list)} tasks.")
        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def _scrape_queue_item(self, category_pair: Tuple[Tuple[str, int, str, int]],
                           search_result_url: str) -> None:
        self.scraping_funcs: ApollonScrapingFunctions

        web_response = self._get_logged_in_web_response(search_result_url, expected_page_type=PageType.SEARCH_RESULT)

        soup_html: BeautifulSoup = get_page_as_soup_html(web_response.text)
        listing_info = product_page_urls, titles, urls_is_sticky, sellers, seller_urls, nrs_of_views, \
                       publication_dates, categories = \
            self.scraping_funcs.get_listing_infos(
                soup_html)

        if len(product_page_urls) == 0:
            if soup_html.text.find(APOLLON_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE) == -1:
                raise AssertionError  # raise error if no logical reason why search result is empty
            else:
                return

        btc_rate, xmr_rate, bch_rate, ltc_rate = self.scraping_funcs.get_cryptocurrency_rates(soup_html)

        for i in range(len(listing_info[1:])):
            assert len(listing_info[i]) == len(listing_info[i - 1])

        for product_url, title, is_sticky, seller, seller_url, nr_of_views, publication_date, category_pair in \
                zip(*listing_info):
            self._db_error_catch_wrapper(self.db_session, product_url, title, is_sticky, seller, seller_url,
                                         nr_of_views, publication_date, category_pair, btc_rate, xmr_rate, bch_rate,
                                         ltc_rate, func=self._scrape_listing)

    def _scrape_listing(self, product_url: str, title: str, is_sticky: bool, seller_name: str,
                        seller_url: str, nr_of_views: int, publication_date: datetime, category_pair: Tuple[Tuple],
                        btc_rate: float, xmr_rate: float, bch_rate: float, ltc_rate: float):
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
        self.scraping_funcs: ApollonScrapingFunctions

        shipping_methods: Tuple[Tuple[str, int, str, float, Optional[str], bool]]

        seller, is_new_seller = self._get_seller(seller_name)

        listing_observation, is_new_listing_observation = self._get_listing_observation(product_url)

        if not is_new_listing_observation:
            return

        is_new_seller_observation = self._get_is_new_seller_observation(seller.id)

        if is_new_seller_observation:
            self._scrape_seller(seller_url, seller, is_new_seller)

        with self.__current_tasks_lock__:
            self.CURRENT_TASKS.discard(seller.id)

        self.print_crawling_debug_message(url=product_url)

        web_response = self._get_logged_in_web_response(product_url, expected_page_type=PageType.LISTING)
        soup_html = get_page_as_soup_html(web_response.text)

        accepts_BTC = True  # appears mandatory to support BTC on Apollon
        fiat_currency = "USD"  # very safely assuming displayed fiat is always in USD
        accepts_BTC_multisig = False  # not supported on Apollon
        ends_in = None  # no sign that Apollon supports time limited listings

        accepts_XMR, accepts_BCH, accepts_LTC = self.scraping_funcs.accepts_currencies(soup_html)
        nr_sold = self.scraping_funcs.get_sales(soup_html)
        fiat_price = self.scraping_funcs.get_fiat_price(soup_html)
        origin_country = self.scraping_funcs.get_origin_country(soup_html)
        destination_countries = self.scraping_funcs.get_destination_countries(soup_html)
        escrow, fifty_percent_finalize_early = self.scraping_funcs.get_payment_method(soup_html)
        quantity_in_stock = self.scraping_funcs.get_quantity_in_stock(soup_html)
        standardized_listing_type: ListingType = self.scraping_funcs.get_standardized_listing_type(soup_html)
        shipping_methods = self.scraping_funcs.get_shipping_methods(soup_html)
        listing_text = self.scraping_funcs.get_listing_text(soup_html)

        self._add_shipping_methods(listing_observation.id, shipping_methods)
        self._add_category_junctions(listing_observation.id, category_pair)

        listing_text_id: int = self._add_text(listing_text)

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

    def _scrape_seller(self, seller_url, seller, is_new_seller):
        self.scraping_funcs: ApollonScrapingFunctions
        self.print_crawling_debug_message(url=seller_url)

        web_response = self._get_logged_in_web_response(seller_url, expected_page_type=PageType.SELLER)
        soup_html = get_page_as_soup_html(web_response.text)

        description = self.scraping_funcs.get_seller_about_description(soup_html)
        email, jabber_id = self.scraping_funcs.get_email_and_jabber_id(soup_html)

        seller_level, trust_level = self.scraping_funcs.get_seller_and_trust_level(soup_html)
        positive_feedback_received_percent = self.scraping_funcs.get_positive_feedback_percent(soup_html)
        registration_date = self.scraping_funcs.get_registration_date(soup_html)
        last_login = self.scraping_funcs.get_last_login(soup_html)
        is_seller = self.scraping_funcs.get_is_seller(soup_html)
        if is_seller:
            sales = self.scraping_funcs.get_sales_by_seller(soup_html)
            fe_enabled = self.scraping_funcs.get_fe_allowed(soup_html)
            autofinalized_orders = None
        else:
            sales = None
            fe_enabled = None
            autofinalized_orders = self.scraping_funcs.get_autofinalized_orders(soup_html)
        orders = self.scraping_funcs.get_orders(soup_html)
        disputes_won, disputes_lost = self.scraping_funcs.get_disputes(soup_html)

        most_recent_feedback_text = self.scraping_funcs.get_most_recent_feedback(soup_html)

        # is_banned: bool = self.scraping_funcs.user_is_banned(soup_html) # TODO: Investigate whether users can have
        # this status on Apollon

        external_market_verifications: Tuple[
            Tuple[str, int, float, float, int, int, int, str]] = self.scraping_funcs.get_external_market_ratings(
            soup_html)

        seller_observation_description = self._add_text(description)

        sub_query = self.db_session.query(func.max(Feedback.date_published).label('max_t')).filter(
            Feedback.seller_id == 5).subquery('sub_query')
        most_recent_stored_feedbacks = self.db_session.query(Feedback).filter(Feedback.seller_id == 5,
                                                                              Feedback.date_published == sub_query.c.max_t).all()

        feedback_categories, feedback_urls = self.scraping_funcs.get_feedback_categories_and_urls(soup_html)
        pgp_url = self.scraping_funcs.get_pgp_url(soup_html)

        assert len(feedback_urls) == len(feedback_categories)

        f: Feedback
        most_recent_stored_feedback_texts = [f.feedback_message_text for f in most_recent_stored_feedbacks]
        if most_recent_feedback_text not in most_recent_stored_feedback_texts:
            for category, feedback_url in zip(feedback_categories, feedback_urls):
                self._scrape_feedback(seller, is_new_seller, category, feedback_url)

        self._scrape_pgp_key(seller, is_new_seller, pgp_url)

        seller_observation = SellerObservation(
            seller_id=seller.id,
            session_id=self.session_id,
            description=seller_observation_description,
            url=seller_url,
            disputes_won=disputes_won,
            disputes_lost=disputes_lost,
            disputes=disputes_lost + disputes_won,
            orders=orders,
            last_online=last_login,
            parenthesis_number=sales,
            positive_feedback_received_percent=positive_feedback_received_percent,
            vendor_level=seller_level,
            trust_level=trust_level,
            email=email,
            xmpp_jabber_id=jabber_id,
            fe_enabled=fe_enabled,
            autofinalized_orders=autofinalized_orders
        )

        if is_new_seller:
            seller.registration_date = registration_date

        self.db_session.add(seller_observation)
        self.db_session.commit()

        self._add_external_market_verifications(seller_observation.id, external_market_verifications)

    def _scrape_feedback(self, seller, is_new_seller, category, url):

        self.scraping_funcs: ApollonScrapingFunctions

        if url:
            self.print_crawling_debug_message(url=url)
            web_response = self._get_logged_in_web_response(url)
            soup_html = get_page_as_soup_html(web_response.text)
        else:
            return

        feedbacks = self.scraping_funcs.get_feedbacks(soup_html)
        # publication_date, title, msg, text_hash, buyer, currency, price, url))
        for publication_date, title, feedback_message_text, text_hash, buyer, currency, price, product_url in feedbacks:
            if not is_new_seller:
                existing_feedback = self.db_session.query(Feedback).filter_by(
                    date_published=publication_date,
                    buyer=buyer,
                    category=category,
                    text_hash=text_hash,
                    currency=currency,
                    market=self.market_id) \
                    .join(Seller, Seller.id == Feedback.seller_id) \
                    .first()

                if existing_feedback:
                    self.db_session.flush()
                    return

            db_feedback = Feedback(
                date_published=publication_date,
                category=category,
                market=self.market_id,
                seller_id=seller.id,
                session_id=self.session_id,
                product_title=title,
                feedback_message_text=feedback_message_text,
                text_hash=text_hash,
                buyer=buyer,
                currency=currency,
                price=price,
                product_url=product_url
            )
            self.db_session.add(db_feedback)

        self.db_session.flush()

        next_feedback_url = self.scraping_funcs.get_next_feedback_url(soup_html)

        if next_feedback_url:
            self._scrape_feedback(seller, is_new_seller, category=category, url=next_feedback_url)

    def _scrape_pgp_key(self, seller, is_new_seller, pgp_url):
        self.scraping_funcs: ApollonScrapingFunctions
        scrape_pgp_this_session = self._should_scrape_pgp_key_this_session(seller, is_new_seller)
        if scrape_pgp_this_session:
            web_response = self._get_logged_in_web_response(pgp_url, expected_page_type=PageType.PGP)
            soup_html = get_page_as_soup_html(web_response.text)
            pgp_key_content = self.scraping_funcs.get_pgp_key(soup_html)
            if pgp_key_content:
                self._add_pgp_key(seller, pgp_key_content)

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
