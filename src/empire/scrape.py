import base64
import hashlib
import time
import traceback
from queue import Empty
from random import shuffle

import requests
from python3_anticaptcha import ImageToTextTask
from requests.cookies import create_cookie

from definitions import EMPIRE_MARKET_URL, EMPIRE_MARKET_ID, DEBUG_MODE, EMPIRE_BASE_CRAWLING_URL, EMPIRE_DIR, \
    EMPIRE_MARKET_LOGIN_URL, PROXIES, ANTI_CAPTCHA_ACCOUNT_KEY, EMPIRE_MARKET_HOME_URL
from src.base import Base, engine, LoggedOutException
from src.base import BaseScraper
from src.empire.functions import EmpireScrapingFunctions as scrapingFunctions
from src.models.country import Country
from src.models.listing_category import ListingCategory
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory
from src.models.listing_observation_country import ListingObservationCountry
from src.models.listing_text import ListingText
from src.models.seller import Seller, SellerObservation
from src.utils import pretty_print_GET

NR_OF_PAGES = 2249

Base.metadata.create_all(engine)


class EmpireScrapingSession(BaseScraper):

    @staticmethod
    def _is_logged_out(response):
        for history_response in response.history:
            if history_response.is_redirect:
                if history_response.raw.headers._container['location'][1] == EMPIRE_MARKET_LOGIN_URL:
                    return True

        return False

    def __init__(self, queue, username, password, db_session, thread_id, session_id=None):
        super().__init__(queue, username, password, db_session, thread_id=thread_id, session_id=session_id)
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
        captcha_solution = ImageToTextTask.ImageToTextTask(
                                anticaptcha_key=ANTI_CAPTCHA_ACCOUNT_KEY
                            ).captcha_handler(captcha_base64=base64_image)["solution"]["text"]
        print("Captcha solved. Solving took " + str(time.time()-time_before_requesting_captcha_solve) + " seconds.")

        login_payload = scrapingFunctions.get_login_payload(soup_html, self.username, self.password, captcha_solution)
        self._get_page_response_and_try_forever(EMPIRE_MARKET_LOGIN_URL, post_data=login_payload)

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
        return {
            "Host": self._get_market_URL(),
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "http://" + self._get_market_URL() + "/login",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _get_web_response(self, url, debug=DEBUG_MODE):
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

            try:
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
                    seller = sellers[k]
                    seller_url = seller_urls[k]

                    existing_listing_observation = self.db_session.query(ListingObservation).filter_by(
                        title=title,
                        seller=seller,
                        session_id=self.session_id
                    ).first()

                    if existing_listing_observation:
                        scrapingFunctions.print_duplicate_debug_message(existing_listing_observation, self.initial_queue_size, self.queue.qsize(), self.thread_id, cookie, parsing_time)
                        self.duplicates_this_session += 1
                        k += 1
                        continue

                    existing_seller = self.db_session.query(SellerObservation).filter_by(
                        name=seller,
                        session_id=self.session_id
                    ).first()

                    if existing_seller:
                        seller_id = existing_seller.id
                    else:
                        seller_id = self._scrape_seller(seller_url)

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
                    vendor_level, trust_level = scrapingFunctions.get_vendor_and_trust_level(soup_html)
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
                        promoted_listing=is_sticky,
                        btc_rate=btc_rate,
                        ltc_rate=ltc_rate,
                        xmr_rate=xmr_rate,
                        seller_id=seller_id,
                        fiat_currency=fiat_currency,
                        price=price,
                        origin_country=origin_country,
                        vendor_level=vendor_level,
                        trust_level=trust_level
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

            except (KeyboardInterrupt, SystemExit, AttributeError, LoggedOutException):
                self._wrap_up_session()
                traceback.print_exc()
                debug_html = None
                tries = 0
                while debug_html is None and tries < 10:
                    try:
                        debug_html = self.web_session.get(EMPIRE_BASE_CRAWLING_URL, proxies=PROXIES, headers=self.headers).text
                        debug_html = "".join(debug_html.split())
                        print(pretty_print_GET(self.web_session.prepare_request(
                        requests.Request('GET', url=EMPIRE_BASE_CRAWLING_URL, headers=self.headers))))
                    except:
                        tries += 1
                print(debug_html)
                raise
            except BaseException as e:
                traceback.print_exc()
                print("Error when trying to parse. ")
                try:
                    print("Product page url: " + str(product_page_url))
                except:
                    pass
                try:
                    print("Search result page url: " + str(search_result_url))
                except:
                    pass

    def _scrape_seller(self, seller_url):
        web_reponse = self._get_web_response(seller_url)
        soup_html = self._get_page_as_soup_html(web_reponse, "saved_empire_user_html")

