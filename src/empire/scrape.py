import base64
import hashlib
import time
import traceback
from datetime import datetime
from queue import Empty
from random import shuffle

from python3_anticaptcha import ImageToTextTask
from requests.cookies import create_cookie
from sqlalchemy.exc import OperationalError
from urllib3.exceptions import NewConnectionError, HTTPError

from definitions import EMPIRE_MARKET_URL, EMPIRE_MARKET_ID, DEBUG_MODE, EMPIRE_DIR, \
    EMPIRE_MARKET_LOGIN_URL, PROXIES, ANTI_CAPTCHA_ACCOUNT_KEY, EMPIRE_MARKET_HOME_URL, EMPIRE_HTTP_HEADERS, engine, \
    Base, DBMS_DISCONNECT_RETRY_INTERVALS
from src.base import BaseScraper, LoggedOutException
from src.empire.functions import EmpireScrapingFunctions as scrapingFunctions
from src.models.country import Country
from src.models.feedback import Feedback
from src.models.listing_category import ListingCategory
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory
from src.models.listing_observation_country import ListingObservationCountry
from src.models.listing_text import ListingText
from src.models.seller import Seller
from src.models.seller_description_text import SellerDescriptionText
from src.models.seller_observation import SellerObservation

asd  = NewConnectionError

Base.metadata.create_all(engine)

class EmpireScrapingSession(BaseScraper):

    @staticmethod
    def _is_logged_out(response):
        for history_response in response.history:
            if history_response.is_redirect:
                if history_response.raw.headers._container['location'][1] == EMPIRE_MARKET_LOGIN_URL:
                    return True

        if response.text.find("Welcome to Empire Market! Please login to access the marketplace.") != -1:
            return True

        return False

    def __init__(self, queue, username, password, db_session, nr_of_threads, thread_id, session_id=None):
        super().__init__(queue, username, password, db_session, nr_of_threads, thread_id=thread_id, session_id=session_id)
        self.logged_out_exceptions = 0

    def _get_working_dir(self):
        return EMPIRE_DIR

    def _login_and_set_cookie(self, response=None, debug=DEBUG_MODE):
        if debug:
            self._set_cookies()
            return

        if not response:
            response = self._get_page_response_and_try_forever(EMPIRE_MARKET_LOGIN_URL)

        soup_html = self._get_page_as_soup_html(response, "saved_empire_login_html")
        image_url = scrapingFunctions.get_captcha_image_url(soup_html)

        image_response = self._get_page_response_and_try_forever(image_url).content
        base64_image = base64.b64encode(image_response).decode("utf-8")

        time_before_requesting_captcha_solve = time.time()
        print("Thread nr. " + str(self.thread_id) + " sending image to anti-catpcha.com API...")
        captcha_solution_response = ImageToTextTask.ImageToTextTask(
                                anticaptcha_key=ANTI_CAPTCHA_ACCOUNT_KEY
                            ).captcha_handler(captcha_base64=base64_image)

        captcha_solution = captcha_solution_response["solution"]["text"]

        print("Captcha solved. Solving took " + str(time.time()-time_before_requesting_captcha_solve) + " seconds.")

        login_payload = scrapingFunctions.get_login_payload(soup_html, self.username, self.password, captcha_solution)
        response = self._get_page_response_and_try_forever(EMPIRE_MARKET_LOGIN_URL, post_data=login_payload)

        if self._is_logged_out(response):
            print("INCORRECTLY SOLVED CAPTCHA, TRYING AGAIN...")
            self.anti_captcha_control.complaint_on_result(int(captcha_solution_response["taskId"]), "image")
            self._login_and_set_cookie(response)

    def populate_queue(self):
        web_response = self._get_page_response_and_try_forever(EMPIRE_MARKET_HOME_URL)
        soup_html = self._get_page_as_soup_html(web_response, file="saved_empire_search_result_html")
        pairs_of_category_base_urls_and_nr_of_listings = scrapingFunctions.get_category_urls_and_nr_of_listings(soup_html)
        task_list = []

        for i in range(0, len(pairs_of_category_base_urls_and_nr_of_listings)):
            nr_of_listings = int(pairs_of_category_base_urls_and_nr_of_listings[i][1])
            url = pairs_of_category_base_urls_and_nr_of_listings[i][0]
            nr_of_pages = nr_of_listings // 15
            for k in range(0, nr_of_pages):
                task_list.append(url + str(k*15))

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.initial_queue_size = self.queue.qsize()
        self.session.initial_queue_size = self.initial_queue_size
        self.db_session.commit()

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

    def _get_market_URL(self):
        return EMPIRE_MARKET_URL

    def _get_market_ID(self):
        return EMPIRE_MARKET_ID

    def _get_headers(self):
        headers = EMPIRE_HTTP_HEADERS
        headers["Host"] = self._get_market_URL()
        headers["Referer"] = "http://" + self._get_market_URL() + "/login"
        return headers

    def _get_web_response(self, url, debug=DEBUG_MODE):
        while True:
            try:
                if debug:
                    return None
                else:
                    response = self.web_session.get(url, proxies=PROXIES, headers=self.headers)

                    tries = 0

                    while tries < 5:
                        if self._is_logged_out(response):
                            tries += 1
                            response = self.web_session.get(url, proxies=PROXIES, headers=self.headers)
                        else:
                            return response

                    self._login_and_set_cookie(response)
                    return self._get_web_response(url)
            except (KeyboardInterrupt, SystemExit, AttributeError, LoggedOutException) as e:
                self._log_and_print_error(e)
                self._wrap_up_session()
                self._print_exception_triggering_request(url)
                raise

            except (HTTPError, BaseException) as e:
                self._log_and_print_error(e)



    def scrape(self):
        time_of_last_response = time.time()

        while True:

            try:
                search_result_url = self.queue.get_nowait()
            except Empty:
                print("Job queue is empty. Wrapping up...")
                self._wrap_up_session()
                return

            parsing_time = time.time() - time_of_last_response
            web_response = self._get_web_response(search_result_url)
            time_of_last_response = time.time()

            soup_html = self._get_page_as_soup_html(web_response, file="saved_empire_search_result_html")
            product_page_urls, urls_is_sticky = scrapingFunctions.get_product_page_urls(soup_html)
            titles, sellers, seller_urls = scrapingFunctions.get_titles_and_sellers(soup_html)
            btc_rate, ltc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)

            assert len(titles) == len(sellers) == len(seller_urls) == len(product_page_urls) == len(urls_is_sticky)

            for i in range(0, len(product_page_urls)):
                title = titles[i]
                seller_name = sellers[i]
                seller_url = seller_urls[i]
                product_page_url = product_page_urls[i]
                is_sticky = urls_is_sticky[i]

                error_data = []
                while True:
                    try:
                        self._scrape_listing(title, seller_name, seller_url, product_page_url,
                                             is_sticky, btc_rate, ltc_rate, xmr_rate, parsing_time)
                        self.db_session.commit()
                        for entry in error_data:
                            self._log_and_print_error(entry[0], updated_date=entry[1], print_error=False)
                        error_data = []
                        break
                    except OperationalError as error:
                        error_data.append([error, datetime.utcnow()])
                        nr_of_errors = len(error_data)
                        highest_index = len(DBMS_DISCONNECT_RETRY_INTERVALS) - 1
                        seconds_until_next_try = DBMS_DISCONNECT_RETRY_INTERVALS[
                            min(nr_of_errors-1, highest_index)]
                        traceback.print_exc()
                        print("Problem with DBMS connection. Retrying in " + str(
                            seconds_until_next_try) + " seconds...")
                        self.db_session.rollback()
                        time.sleep(seconds_until_next_try)
                    

    def _scrape_seller(self, seller_observation, seller, is_new_seller):
        seller_url = seller_observation.url
        seller_name = seller.name

        scrapingFunctions.print_crawling_debug_message(seller_url, self.initial_queue_size, self.queue.qsize()
                                                       ,self.thread_id, self._get_cookie_string(), "N/A")
        web_response = self._get_web_response(seller_url)

        soup_html = self._get_page_as_soup_html(web_response, "saved_empire_user_html")

        feedback_categories, feedback_urls = scrapingFunctions.get_feedback_categories_and_urls(soup_html)
        assert len(feedback_urls) == len(feedback_categories)

        for i in range(0, len(feedback_categories)):
            self._scrape_feedback(seller_observation, seller, feedback_categories[i], feedback_urls[i])

        description = scrapingFunctions.get_seller_about_description(soup_html, seller_name)

        disputes, orders, spendings, feedback_left,\
        feedback_percent_positive, last_online = scrapingFunctions.get_buyer_statistics(soup_html)

        positive_1m, positive_6m, positive_12m,\
        neutral_1m, neutral_6m, neutral_12m,\
        negative_1m, negative_6m, negative_12m = scrapingFunctions.get_seller_statistics(soup_html)

        stealth_rating, quality_rating, value_price_rating = scrapingFunctions.get_star_ratings(soup_html)

        parenthesis_number, vendor_level, trust_level = scrapingFunctions.get_parenthesis_number_and_vendor_and_trust_level(soup_html)

        dream_market_successful_sales, dream_market_star_rating,\
        positive_feedback_received_percent, registration_date = scrapingFunctions.get_mid_user_info(soup_html)


        existing_seller_description_text = self.db_session.query(SellerDescriptionText).filter_by(
                            id=hashlib.md5(description.encode('utf-8')).hexdigest()).first()

        if existing_seller_description_text:
            seller_observation.description = existing_seller_description_text.id
        else:
            seller_description_text = SellerDescriptionText(
                id=hashlib.md5(description.encode('utf-8')).hexdigest(),
                text=description
            )
            self.db_session.add(seller_description_text)
            self.db_session.flush()
            seller_observation.description = seller_description_text.id

        seller_observation.disputes = disputes
        seller_observation.orders = orders
        seller_observation.spendings = spendings
        seller_observation.feedback_left = feedback_left
        seller_observation.feedback_percent_positive = feedback_percent_positive
        seller_observation.last_online = last_online

        seller_observation.parenthesis_number = parenthesis_number
        seller_observation.dream_market_successful_sales = dream_market_successful_sales
        seller_observation.dream_market_star_rating = dream_market_star_rating
        seller_observation.positive_feedback_received_percent = positive_feedback_received_percent

        seller_observation.positive_1m = positive_1m
        seller_observation.positive_6m = positive_6m
        seller_observation.positive_12m = positive_12m

        seller_observation.neutral_1m = neutral_1m
        seller_observation.neutral_6m = neutral_6m
        seller_observation.neutral_12m = neutral_12m

        seller_observation.negative_1m = negative_1m
        seller_observation.negative_6m = negative_6m
        seller_observation.negative_12m = negative_12m

        seller_observation.stealth_rating = stealth_rating
        seller_observation.quality_rating = quality_rating
        seller_observation.value_price_rating = value_price_rating

        seller_observation.vendor_level = vendor_level
        seller_observation.trust_level = trust_level

        if is_new_seller:
            seller.registration_date = registration_date

        self.db_session.flush()

    def _scrape_feedback(self, seller_observation, seller, category, url):

        scrapingFunctions.print_crawling_debug_message(url, self.initial_queue_size, self.queue.qsize()
                                                       , self.thread_id, self._get_cookie_string(), "N/A")

        web_response = self._get_web_response(url)
        soup_html = self._get_page_as_soup_html(web_response, "saved_empire_user_positive_feedback")

        feedback_array = scrapingFunctions.get_feedbacks(soup_html)

        for feedback in feedback_array:
            existing_feedback = self.db_session.query(Feedback).filter_by(
                            date_published=feedback["date_published"],
                            buyer=feedback["buyer"],
                            category=category,
                            text_hash=hashlib.md5((feedback["feedback_message"]+feedback["seller_response_message"]).encode('utf-8')).hexdigest()[:8],
                            market=self.market_id)\
                            .join(Seller, Seller.id == Feedback.seller_id)\
                            .first()

            if existing_feedback:
                return

            else:
                db_feedback = Feedback(
                    date_published=feedback["date_published"],
                    category=category,
                    market=self.market_id,
                    seller_id=seller.id,
                    session_id=self.session_id,
                    product_url=feedback["product_url"],
                    feedback_message_text=feedback["feedback_message"],
                    seller_response_message=feedback["seller_response_message"],
                    text_hash=hashlib.md5((feedback["feedback_message"]+feedback["seller_response_message"]).encode('utf-8')).hexdigest()[:8],
                    buyer=feedback["buyer"],
                    currency=feedback["currency"],
                    price=feedback["price"]
                )
                self.db_session.add(db_feedback)

        self.db_session.flush()

        next_url_with_feeback = scrapingFunctions.get_next_feedback_page(soup_html)

        if next_url_with_feeback and not DEBUG_MODE:
            self._scrape_feedback(seller_observation, seller, category, next_url_with_feeback)

    def _scrape_listing(self, title, seller_name, seller_url, product_page_url, is_sticky,
                        btc_rate, ltc_rate, xmr_rate, parsing_time):

        cookie = self._get_cookie_string()

        existing_seller = self.db_session.query(Seller) \
            .filter_by(name=seller_name).first()

        if existing_seller:
            seller = existing_seller
            is_new_seller = False
        else:
            seller = Seller(name=seller_name, market=self.market_id)
            self.db_session.add(seller)
            self.db_session.flush()
            is_new_seller = True

        existing_listing_observation = self.db_session.query(ListingObservation) \
            .filter(ListingObservation.session_id == self.session_id) \
            .filter(ListingObservation.title == title) \
            .join(Seller) \
            .filter(ListingObservation.seller_id == Seller.id) \
            .filter(Seller.name == seller_name) \
            .first()

        if existing_listing_observation:
            scrapingFunctions.print_duplicate_debug_message(existing_listing_observation, self.initial_queue_size,
                                                            self.queue.qsize(), self.thread_id, cookie, parsing_time)
            self.duplicates_this_session += 1
            return

        existing_seller_observation = self.db_session.query(SellerObservation) \
            .filter(SellerObservation.session_id == self.session_id) \
            .join(Seller) \
            .filter(Seller.name == seller_name) \
            .filter(SellerObservation.seller_id == Seller.id) \
            .first()

        if not existing_seller_observation:
            seller_observation = SellerObservation(
                seller_id=seller.id,
                session_id=self.session_id,
                url=seller_url,
                market=self.market_id
            )

            self.db_session.add(seller_observation)
            self.db_session.flush()
            self._scrape_seller(seller_observation, seller, is_new_seller)



        scrapingFunctions.print_crawling_debug_message(product_page_url, self.initial_queue_size, self.queue.qsize(),
                                                       self.thread_id, cookie, parsing_time)

        web_response = self._get_web_response(product_page_url)

        soup_html = self._get_page_as_soup_html(web_response, 'saved_empire_html', DEBUG_MODE)

        session_id = self.session_id
        listing_text = scrapingFunctions.get_description(soup_html)
        listing_text_id = hashlib.md5(listing_text.encode('utf-8')).hexdigest()
        categories, website_category_ids = scrapingFunctions.get_categories_and_ids(soup_html)
        accepts_BTC, accepts_LTC, accepts_XMR = scrapingFunctions.accepts_currencies(soup_html)
        nr_sold, nr_sold_since_date = scrapingFunctions.get_nr_sold_since_date(soup_html)
        fiat_currency, price = scrapingFunctions.get_fiat_currency_and_price(soup_html)
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        db_category_ids = []

        for i in range(0, len(categories)):
            category = self.db_session.query(ListingCategory).filter_by(
                website_id=website_category_ids[i],
                name=categories[i],
                market=self.market_id).first()

            if not category:
                category = ListingCategory(
                    website_id=website_category_ids[i],
                    name=categories[i],
                    market=self.market_id
                )
                self.db_session.add(category)
                self.db_session.flush()

            db_category_ids.append(category.id)

        self.db_session.merge(ListingText(
            id=listing_text_id,
            text=listing_text
        ))

        self.db_session.merge(Country(
            id=origin_country
        ))

        self.db_session.flush()

        listing_observation = ListingObservation(
            session_id=session_id,
            listing_text_id=listing_text_id,
            title=title,
            btc=accepts_BTC,
            ltc=accepts_LTC,
            xmr=accepts_XMR,
            nr_sold=nr_sold,
            nr_sold_since_date=nr_sold_since_date,
            promoted_listing=is_sticky,
            url=product_page_url,
            btc_rate=btc_rate,
            ltc_rate=ltc_rate,
            xmr_rate=xmr_rate,
            seller_id=seller.id,
            fiat_currency=fiat_currency,
            price=price,
            origin_country=origin_country
        )

        self.db_session.add(listing_observation)

        self.db_session.flush()

        for destination_country in destination_countries:
            self.db_session.merge(Country(
                id=destination_country
            ))

            self.db_session.flush()

            self.db_session.add(ListingObservationCountry(
                listing_observation_id=listing_observation.id,
                country_id=destination_country
            ))

        for db_category_id in db_category_ids:
            self.db_session.add(ListingObservationCategory(
                listing_observation_id=listing_observation.id,
                category_id=db_category_id
            ))
