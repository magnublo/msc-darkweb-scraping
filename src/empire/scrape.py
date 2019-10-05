import base64
import hashlib
import time
import traceback
from queue import Empty
from random import shuffle

import requests
from python3_anticaptcha import ImageToTextTask
from requests.cookies import create_cookie

from definitions import EMPIRE_MARKET_URL, EMPIRE_MARKET_ID, DEBUG_MODE, EMPIRE_DIR, \
    EMPIRE_MARKET_LOGIN_URL, PROXIES, ANTI_CAPTCHA_ACCOUNT_KEY, EMPIRE_MARKET_HOME_URL, EMPIRE_HTTP_HEADERS, engine, \
    Base
from src.base import BaseScraper, LoggedOutException
from src.empire.functions import EmpireScrapingFunctions as scrapingFunctions
from src.models.country import Country
from src.models.error import Error
from src.models.feedback import Feedback
from src.models.listing_category import ListingCategory
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory
from src.models.listing_observation_country import ListingObservationCountry
from src.models.listing_text import ListingText
from src.models.seller_description_text import SellerDescriptionText
from src.models.seller_observation import SellerObservation
from src.models.seller_observation_feedback import SellerObservationFeedback
from src.utils import pretty_print_GET

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
            except (KeyboardInterrupt, SystemExit, AttributeError, LoggedOutException):
                self.db_session.add(Error(session_id=self.session_id, thread_id=self.thread_id, text=traceback.format_exc()))
                self.db_session.commit()
                time.sleep(2)
                self._wrap_up_session()
                traceback.print_exc()
                debug_html = None
                tries = 0
                while debug_html is None and tries < 10:
                    try:
                        debug_html = self.web_session.get(url, proxies=PROXIES, headers=self.headers).text
                        debug_html = "".join(debug_html.split())
                        print(pretty_print_GET(self.web_session.prepare_request(
                            requests.Request('GET', url=url, headers=self.headers))))
                    except:
                        tries += 1
                print(debug_html)
                raise

            except BaseException as e:
                self.db_session.add(
                    Error(session_id=self.session_id, thread_id=self.thread_id, text=traceback.format_exc()))
                self.db_session.commit()
                time.sleep(2)
                traceback.print_exc()


    def scrape(self):
        time_of_last_response = time.time()
        k = 0

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
            cookie = self._get_cookie_string()
            soup_html = self._get_page_as_soup_html(web_response, file="saved_empire_search_result_html")
            product_page_urls, urls_is_sticky = scrapingFunctions.get_product_page_urls(soup_html)
            titles, sellers, seller_urls = scrapingFunctions.get_titles_and_sellers(soup_html)
            btc_rate, ltc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)

            while k < len(product_page_urls):
                title = titles[k]
                seller_name = sellers[k]
                seller_url = seller_urls[k]

                existing_listing_observation = self.db_session.query(ListingObservation) \
                    .filter(ListingObservation.session_id == self.session_id) \
                    .join(SellerObservation)\
                    .filter(ListingObservation.seller_id == SellerObservation.id)\
                    .filter(SellerObservation.name == seller_name)\
                    .filter(ListingObservation.title == title)\
                    .first()

                if existing_listing_observation:
                    scrapingFunctions.print_duplicate_debug_message(existing_listing_observation, self.initial_queue_size, self.queue.qsize(), self.thread_id, cookie, parsing_time)
                    self.duplicates_this_session += 1
                    k += 1
                    continue

                existing_seller = self.db_session.query(SellerObservation).filter_by(
                    name=seller_name,
                    session_id=self.session_id
                ).first()

                if existing_seller:
                    seller_id = existing_seller.id
                else:
                    seller_observation = SellerObservation(
                        name=seller_name,
                        session_id=self.session_id,
                        url=seller_url,
                        market=self.market_id
                    )
                    self.db_session.add(seller_observation)
                    self.db_session.commit()
                    self._scrape_seller(seller_observation)
                    seller_id = seller_observation.id

                product_page_url = product_page_urls[k]

                scrapingFunctions.print_crawling_debug_message(product_page_url, self.initial_queue_size, self.queue.qsize(), self.thread_id, cookie, parsing_time)

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
                is_sticky = urls_is_sticky[k]

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
                    seller_id=seller_id,
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


                self.db_session.commit()
                k += 1

            k = 0

    def _scrape_seller(self, seller_observation):
        seller_url = seller_observation.url
        seller_name = seller_observation.name

        scrapingFunctions.print_crawling_debug_message(seller_url, self.initial_queue_size, self.queue.qsize()
                                                       ,self.thread_id, self._get_cookie_string(), "N/A")
        web_response = self._get_web_response(seller_url)

        soup_html = self._get_page_as_soup_html(web_response, "saved_empire_user_html")

        feedback_categories, feedback_urls = scrapingFunctions.get_feedback_categories_and_urls(soup_html)
        assert len(feedback_urls) == len(feedback_categories)

        for i in range(0, len(feedback_categories)):
            self._scrape_feedback(seller_observation, feedback_categories[i], feedback_urls[i])

        description = scrapingFunctions.get_seller_about_description(soup_html, seller_name)

        disputes, orders, spendings, feedback_left,\
        feedback_percent_positive, last_online = scrapingFunctions.get_buyer_statistics(soup_html)

        positive_1m, positive_6m, positive_12m,\
        neutral_1m, neutral_6m, neutral_12m,\
        negative_1m, negative_6m, negative_12m = scrapingFunctions.get_seller_statistics(soup_html)

        stealth_rating, quality_rating, value_price_rating = scrapingFunctions.get_star_ratings(soup_html)

        vendor_level, trust_level = scrapingFunctions.get_vendor_and_trust_level(soup_html)

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
            self.db_session.commit()
            seller_observation.description = seller_description_text.id

        seller_observation.disputes = disputes
        seller_observation.orders = orders
        seller_observation.spendings = spendings
        seller_observation.feedback_left = feedback_left
        seller_observation.feedback_percent_positive = feedback_percent_positive
        seller_observation.last_online = last_online

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

        self.db_session.commit()

    def _scrape_feedback(self, seller_observation, category, url):

        scrapingFunctions.print_crawling_debug_message(url, self.initial_queue_size, self.queue.qsize()
                                                       , self.thread_id, self._get_cookie_string(), "N/A")

        web_response = self._get_web_response(url)

        soup_html = self._get_page_as_soup_html(web_response, "saved_empire_user_negative_feedback")

        feedback_array = scrapingFunctions.get_feedbacks(soup_html)

        db_feedbacks = []

        for feedback in feedback_array:
            existing_feedback = self.db_session.query(Feedback).filter_by(
                            date_published=feedback["date_published"],
                            buyer=feedback["buyer"],
                            category=category,
                            text_hash=hashlib.md5((feedback["feedback_message"]+feedback["seller_response_message"]).encode('utf-8')).hexdigest()[:8],
                            market=self.market_id)\
                            .join(SellerObservationFeedback)\
                            .filter(SellerObservationFeedback.feedback_id == Feedback.id)\
                            .join(SellerObservation)\
                            .filter(SellerObservationFeedback.seller_observation_id == SellerObservation.id)\
                            .filter(SellerObservation.name == seller_observation.name)\
                            .first()

            if not existing_feedback:
                db_feedback = Feedback(
                    date_published=feedback["date_published"],
                    category=category,
                    market=self.market_id,
                    feedback_message_text=feedback["feedback_message"],
                    seller_response_message=feedback["seller_response_message"],
                    text_hash=hashlib.md5((feedback["feedback_message"]+feedback["seller_response_message"]).encode('utf-8')).hexdigest()[:8],
                    buyer=feedback["buyer"],
                    currency=feedback["currency"],
                    price=feedback["price"]
                )
                self.db_session.add(db_feedback)
                db_feedbacks.append(db_feedback)
            else:
                db_feedbacks.append(existing_feedback)

        self.db_session.commit()
        assert len(db_feedbacks) == len(feedback_array)

        for i in range(0, len(db_feedbacks)):
            db_feedback = db_feedbacks[i]
            feedback = feedback_array[i]
            seller_observation_feedback = SellerObservationFeedback(
                seller_observation_id=seller_observation.id,
                feedback_id=db_feedback.id,
                product_url=feedback["product_url"]
            )
            self.db_session.add(seller_observation_feedback)

        self.db_session.commit()
