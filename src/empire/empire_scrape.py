import hashlib
from math import ceil
from multiprocessing import Queue
from random import shuffle
from typing import List, Tuple, Type

import requests
from requests.cookies import create_cookie
from sqlalchemy import func

from definitions import EMPIRE_MARKET_URL, EMPIRE_MARKET_ID, EMPIRE_SRC_DIR, \
    EMPIRE_MARKET_LOGIN_URL, EMPIRE_MARKET_HOME_URL, EMPIRE_HTTP_HEADERS, \
    FEEDBACK_TEXT_HASH_COLUMN_LENGTH, EMPIRE_MARKET_LOGIN_PHRASE, \
    EMPIRE_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE, MD5_HASH_STRING_ENCODING
from environment_settings import DEBUG_MODE
from src.base_functions import BaseFunctions
from src.base_scraper import BaseScraper
from src.db_utils import get_column_name
from src.empire.empire_functions import EmpireScrapingFunctions
from src.models.country import Country
from src.models.feedback import Feedback
from src.models.listing_text import ListingText
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.verified_external_account import VerifiedExternalAccount
from src.utils import get_page_as_soup_html


class EmpireScrapingSession(BaseScraper):

    def _get_anti_captcha_kwargs(self) -> dict:
        return {'numeric': 1}

    def __init__(self, queue: Queue, username: str, password: str, nr_of_threads: int, thread_id: int, proxy: dict,
                 session_id: int, mirror_base_url: str):
        super().__init__(queue, username, password, nr_of_threads, thread_id=thread_id, proxy=proxy,
                         session_id=session_id, mirror_base_url=mirror_base_url)

    def get_base_url(self) -> str:
        raise NotImplementedError('')

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        return EmpireScrapingFunctions

    def _get_web_session(self) -> requests.Session:
        return requests.Session()

    def _get_working_dir(self) -> str:
        return EMPIRE_SRC_DIR

    def _get_login_url(self) -> str:
        return EMPIRE_MARKET_LOGIN_URL

    def _get_is_logged_out_phrase(self) -> str:
        return EMPIRE_MARKET_LOGIN_PHRASE

    def _set_cookies(self):

        cookie = create_cookie(
            domain=EMPIRE_MARKET_URL,
            name='ab',
            value='1cc735432450e28fa3333f2904cd5ae3')

        self.web_session.cookies.set_cookie(
            cookie
        )

        cookie = create_cookie(
            domain=EMPIRE_MARKET_URL,
            name='shop',
            value='ske8ud8vnlrsq18vi6r7rhss4vbnukv0')

        self.web_session.cookies.set_cookie(
            cookie
        )

        self.cookie = self._get_cookie_string()

    def _get_market_URL(self) -> str:
        return EMPIRE_MARKET_URL

    def _get_market_id(self) -> str:
        return EMPIRE_MARKET_ID

    def _get_headers(self) -> dict:
        headers = EMPIRE_HTTP_HEADERS
        headers["Host"] = self._get_market_URL()
        headers["Referer"] = "http://" + self._get_market_URL() + "/login"
        return headers

    def populate_queue(self):
        web_response = self._get_logged_in_web_response(EMPIRE_MARKET_HOME_URL)
        soup_html = get_page_as_soup_html(web_response)
        pairs_of_category_base_urls_and_nr_of_listings = self.scraping_funcs.get_category_urls_and_nr_of_listings(
            soup_html)
        task_list = []

        for i in range(0, len(pairs_of_category_base_urls_and_nr_of_listings)):
            nr_of_listings = int(pairs_of_category_base_urls_and_nr_of_listings[i][1])
            url = pairs_of_category_base_urls_and_nr_of_listings[i][0]
            nr_of_pages = ceil(nr_of_listings / 15)
            for k in range(0, nr_of_pages):
                task_list.append(url + str(k * 15))

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def _scrape_listing(self, title, seller_name, seller_url, product_page_url, is_sticky,
                        btc_rate, ltc_rate, xmr_rate):

        # TODO: Scrape shipping methods, accepts_multisig, in_stock, product_type, ends_in, bulk price

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

        listing_text = self.scraping_funcs.get_description(soup_html)
        listing_text_id = hashlib.md5(listing_text.encode(MD5_HASH_STRING_ENCODING)).hexdigest()
        categories, website_category_ids = self.scraping_funcs.get_categories_and_ids(soup_html)
        accepts_BTC, accepts_LTC, accepts_XMR = self.scraping_funcs.accepts_currencies(soup_html)
        nr_sold, nr_sold_since_date = self.scraping_funcs.get_nr_sold_since_date(soup_html)
        fiat_currency, price = self.scraping_funcs.get_fiat_currency_and_price(soup_html)
        origin_country, destination_countries, escrow = \
            self.scraping_funcs.get_origin_country_and_destinations_and_payment_type(
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
        listing_observation.escrow = escrow

        self.db_session.flush()

    def _scrape_seller(self, seller_url, seller, is_new_seller):
        self.print_crawling_debug_message(url=seller_url)

        web_response = self._get_logged_in_web_response(seller_url)
        soup_html = get_page_as_soup_html(web_response)

        seller_name = seller.name
        description = self.scraping_funcs.get_seller_about_description(soup_html, seller_name)

        disputes, orders, spendings, feedback_left, \
        feedback_percent_positive, last_online = self.scraping_funcs.get_buyer_statistics(soup_html)

        positive_1m, positive_6m, positive_12m, \
        neutral_1m, neutral_6m, neutral_12m, \
        negative_1m, negative_6m, negative_12m = self.scraping_funcs.get_seller_statistics(soup_html)

        stealth_rating, quality_rating, value_price_rating = self.scraping_funcs.get_star_ratings(soup_html)

        parenthesis_number, vendor_level, trust_level = \
            self.scraping_funcs.get_parenthesis_number_and_vendor_and_trust_level(
                soup_html)

        positive_feedback_received_percent, registration_date = self.scraping_funcs.get_mid_user_info(soup_html)

        external_market_verifications: List[Tuple[str, int, float]] = self.scraping_funcs.get_external_market_ratings(
            soup_html)

        seller_observation_description = self._add_seller_observation_description(description)

        previous_seller_observation = self.db_session.query(SellerObservation).filter(
            SellerObservation.created_date == self.db_session.query(func.max(SellerObservation.created_date)).filter(
                SellerObservation.seller_id == seller.id).subquery().as_scalar()).first()

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
            trust_level=trust_level
        )

        if is_new_seller:
            seller.registration_date = registration_date

        self.db_session.add(seller_observation)
        self.db_session.flush()

        self._add_external_market_verifications(seller_observation.id, external_market_verifications)

    def _scrape_feedback(self, seller, is_new_seller, category, url):

        self.print_crawling_debug_message(url=url)

        web_response = self._get_logged_in_web_response(url)

        soup_html = get_page_as_soup_html(web_response)

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
                    (feedback["feedback_message"] + feedback["seller_response_message"]).encode(MD5_HASH_STRING_ENCODING)).hexdigest()[
                          :FEEDBACK_TEXT_HASH_COLUMN_LENGTH],
                buyer=feedback["buyer"],
                currency=feedback["currency"],
                price=feedback["price"]
            )
            self.db_session.add(db_feedback)

        self.db_session.flush()

        next_url_with_feeback = self.scraping_funcs.get_next_feedback_page(soup_html)

        if next_url_with_feeback and not DEBUG_MODE:
            self._scrape_feedback(seller, is_new_seller, category, next_url_with_feeback)

    def _scrape_pgp_key(self, seller: Seller, is_new_seller: bool, url: str) -> None:

        scrape_pgp_this_session = self._should_scrape_pgp_key_this_session(seller, is_new_seller)

        if scrape_pgp_this_session:
            web_response = self._get_logged_in_web_response(url)
            soup_html = get_page_as_soup_html(web_response)
            pgp_key_content = self.scraping_funcs.get_pgp_key(soup_html)
            self._add_pgp_key(seller, pgp_key_content)

    def _scrape_queue_item(self, search_result_url: str):
        web_response = self._get_logged_in_web_response(search_result_url)

        soup_html = get_page_as_soup_html(web_response)
        product_page_urls, urls_is_sticky = self.scraping_funcs.get_product_page_urls(soup_html)

        if len(product_page_urls) == 0:
            if soup_html.text.find(EMPIRE_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE) == -1:
                raise AssertionError  # raise error if no logical reason why search result is empty
            else:
                return

        titles, sellers, seller_urls = self.scraping_funcs.get_titles_and_sellers(soup_html)
        btc_rate, ltc_rate, xmr_rate = self.scraping_funcs.get_cryptocurrency_rates(soup_html)

        assert len(titles) == len(sellers) == len(seller_urls) == len(product_page_urls) == len(urls_is_sticky)

        for title, seller_name, seller_url, product_page_url, is_sticky in zip(titles, sellers, seller_urls,
                                                                               product_page_urls,
                                                                               urls_is_sticky):
            self._db_error_catch_wrapper(title, seller_name, seller_url, product_page_url,
                                         is_sticky, btc_rate, ltc_rate, xmr_rate, func=self._scrape_listing)


    def _add_external_market_verifications(self, seller_observation_id: int,
                                           external_market_verifications: List[Tuple[str, int, float]]) -> None:

        for market_id, sales, rating in external_market_verifications:
            self.db_session.add(
                                VerifiedExternalAccount(
                                        seller_observation_id=seller_observation_id, market_id=market_id,
                                        confirmed_sales=sales, rating=rating)
                                )
            self.db_session.flush()

