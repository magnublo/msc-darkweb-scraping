import base64
import hashlib
import pickle
import sys
import traceback
from _mysql_connector import MySQLError
from abc import abstractmethod
from datetime import datetime
from multiprocessing import Queue
from time import sleep
from time import time
from typing import Callable, List, Tuple, Union, Type

import requests
from python3_anticaptcha import AntiCaptchaControl, ImageToTextTask
from requests import Response
from requests.cookies import RequestsCookieJar
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from urllib3.exceptions import HTTPError

from definitions import ANTI_CAPTCHA_ACCOUNT_KEY, MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD, \
    ERROR_FINGER_PRINT_COLUMN_LENGTH, DBMS_DISCONNECT_RETRY_INTERVALS, ONE_DAY, \
    RESCRAPE_PGP_KEY_INTERVAL, MD5_HASH_STRING_ENCODING, DEAD_MIRROR_TIMEOUT
from src.base_functions import BaseFunctions
from src.base_logger import BaseClassWithLogger
from src.db_utils import shorten_and_sanitize_for_medium_text_column, get_engine, get_db_session, sanitize_error, \
    get_column_name
from src.models.bulk_price import BulkPrice
from src.models.captcha_solution import CaptchaSolution
from src.models.country import Country
from src.models.error import Error
from src.models.listing_category import ListingCategory
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory
from src.models.listing_observation_country import ListingObservationCountry
from src.models.pgp_key import PGPKey
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_description_text import SellerDescriptionText
from src.models.seller_observation import SellerObservation
from src.models.shipping_method import ShippingMethod
from src.models.web_session_cookie import WebSessionCookie
from src.utils import pretty_print_GET, get_error_string, print_error_to_file, is_internal_server_error, \
    InternalServerErrorException, is_bad_gateway, BadGatewayException, error_is_sqlalchemy_error, \
    GenericException, get_seconds_until_midnight, get_page_as_soup_html


class BaseScraper(BaseClassWithLogger):

    def __init__(self, queue: Queue, username: str, password: str, nr_of_threads: int, thread_id: int,
                 proxy: dict, session_id: int, mirror_base_url: str):
        super().__init__()
        engine = get_engine()
        self.scraping_funcs = self._get_scraping_funcs()
        self.mirror_base_url = mirror_base_url
        self.login_url = self._get_login_url()
        self.is_logged_out_phrase = self._get_is_logged_out_phrase()
        self.working_dir = self._get_working_dir()
        self.proxy = proxy
        self.logged_out_exceptions = 0
        self.db_session = get_db_session(engine)
        self.username = username  # TODO: Make username and password Lists, and let BaseScraper use a pool of them
        self.password = password
        self.thread_id = thread_id
        self.nr_of_threads = nr_of_threads
        self.anti_captcha_control = AntiCaptchaControl.AntiCaptchaControl(ANTI_CAPTCHA_ACCOUNT_KEY)
        self.headers = self._get_headers()
        self.queue = queue
        self.market_id = self._get_market_id()
        self.start_time = time()
        self.duplicates_this_session = 0
        self.web_session: requests.Session = self._instantiate_web_session()
        self.cookie_string = self._get_cookie_string()
        self.initial_queue_size = self.queue.qsize()
        self.time_last_received_response = 0

        if session_id:
            while True:
                try:
                    self.db_session.rollback()
                    scraping_session = self.db_session.query(ScrapingSession).filter_by(
                        id=session_id).first()
                    self.session_id = scraping_session.id
                    self.db_session.expunge(scraping_session)
                    break
                except (SQLAlchemyError, MySQLError, AttributeError, SystemError):
                    print("Thread nr. " + str(self.thread_id) + " has problem querying session id in DB. Retrying...")
                    sleep(5)
        else:
            self.session_id = self._initiate_session()

    def scrape(self):
        while not self.queue.empty():
            queue_item = self.queue.get(timeout=1)
            self._generic_error_catch_wrapper(*queue_item, func=self._scrape_queue_item)

        print("Job queue is empty. Wrapping up...")
        self._wrap_up_session()

    def _initiate_session(self) -> int:
        from socket import getfqdn
        scraping_session = ScrapingSession(
            market=self.market_id,
            duplicates_encountered=self.duplicates_this_session,
            nr_of_threads=self.nr_of_threads,
            host_system_fqdn=getfqdn()
        )
        self.db_session.add(scraping_session)
        self.db_session.commit()
        session_id = scraping_session.id
        print("Thread nr. " + str(self.thread_id) + " initiated scraping_session with ID: " + str(scraping_session.id))
        self.db_session.expunge(scraping_session)
        return session_id

    def _log_and_print_error(self, error_object, error_string, updated_date=None, print_error=True) -> None:

        if print_error:
            self.logger.debug(error_string)

        if error_object is None:
            error_type = None
        else:
            error_type = type(error_object).__name__

        errors = self.db_session.query(Error).filter_by(thread_id=self.thread_id, type=error_type).order_by(
            Error.updated_date.asc())

        finger_print = hashlib.md5((error_type + str(time())).encode(MD5_HASH_STRING_ENCODING)) \
                           .hexdigest()[0:ERROR_FINGER_PRINT_COLUMN_LENGTH]

        error_string = sanitize_error(error_string, locals().keys())
        error_string = shorten_and_sanitize_for_medium_text_column(error_string)

        if errors.count() >= MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD:
            error = errors.first()
            error.updated_date = updated_date
            error.session_id = self.session_id
            error.thread_id = self.thread_id
            error.type = error_type
            error.text = error_string
            error.finger_print = finger_print
        else:
            error = Error(updated_date=updated_date, session_id=self.session_id, thread_id=self.thread_id,
                          type=error_type, text=error_string, finger_print=finger_print)
            self.db_session.add(error)
        try:
            self.db_session.commit()
        except ProgrammingError:
            meta_error_string = get_error_string(self, traceback.format_exc(), sys.exc_info())
            print_error_to_file(self.thread_id, meta_error_string, "meta")
        sleep(2)

    def _wrap_up_session(self) -> None:
        scraping_session = self.db_session.query(ScrapingSession).filter(
            ScrapingSession.id == self.session_id).first()

        scraping_session.time_finished = datetime.fromtimestamp(time())
        scraping_session.duplicates_encountered += self.duplicates_this_session
        scraping_session.exited_gracefully = True

        while True:
            try:
                self.db_session.merge(scraping_session)
                self.db_session.commit()
                break
            except:
                sleep(10)

        self.db_session.expunge_all()
        self.db_session.close()

    def _get_cookie_string(self) -> str:
        request_as_string = pretty_print_GET(self.web_session.prepare_request(
            requests.Request('GET', url="http://" + self.headers["Host"], headers=self.headers)))
        lines = request_as_string.split("\n")
        for line in lines:
            if line[0:7].lower() == "cookie:":
                return line.strip().lower()

    def _get_wait_interval(self, error_data) -> int:
        nr_of_errors = max(len(error_data) - 1, 0)
        highest_index = len(DBMS_DISCONNECT_RETRY_INTERVALS) - 1
        seconds_until_next_try = DBMS_DISCONNECT_RETRY_INTERVALS[
                                     min(nr_of_errors - 1, highest_index)] + self.thread_id * 2
        return seconds_until_next_try

    def _get_seller(self, seller_name: str) -> Tuple[Seller, bool]:
        existing_seller = self.db_session.query(Seller) \
            .filter_by(name=seller_name, market=self.market_id).first()

        if existing_seller:
            seller = existing_seller
            return seller, False
        else:
            seller = Seller(name=seller_name, market=self.market_id)
            self.db_session.add(seller)
            self.db_session.flush()
            return seller, True

    def _get_listing_observation(self, title: str, seller_id: int) -> Tuple[ListingObservation, bool]:
        existing_listing_observation = self.db_session.query(ListingObservation) \
            .filter(ListingObservation.session_id == self.session_id, ListingObservation.title == title,
                    ListingObservation.seller_id == seller_id).first()

        if existing_listing_observation:
            self.print_crawling_debug_message(existing_listing_observation=existing_listing_observation)
            self.duplicates_this_session += 1
            listing_observation = existing_listing_observation
            is_new_listing_observation = False
        else:
            listing_observation = ListingObservation(session_id=self.session_id,
                                                     thread_id=self.thread_id,
                                                     title=title,
                                                     seller_id=seller_id)
            is_new_listing_observation = True
            self.db_session.add(listing_observation)
            self.db_session.flush()

        return listing_observation, is_new_listing_observation

    def _exists_seller_observation_from_this_session(self, seller_id: int) -> bool:
        existing_seller_observation = self.db_session.query(SellerObservation) \
            .filter(SellerObservation.session_id == self.session_id) \
            .join(Seller) \
            .filter(SellerObservation.seller_id == seller_id) \
            .first()

        if existing_seller_observation:
            return False
        else:
            return True

    def _add_category_junctions(self, categories: List[str], website_category_ids: List[Union[int, None]],
                                listing_observation_id: int) -> None:

        for i in range(0, len(categories)):
            category = self.db_session.query(ListingCategory).filter(
                ListingCategory.website_id == website_category_ids[i],
                ListingCategory.name == categories[i],
                ListingCategory.market == self.market_id).first()

            if not category:
                category = ListingCategory(
                    website_id=website_category_ids[i],
                    name=categories[i],
                    market=self.market_id
                )
                self.db_session.add(category)
                self.db_session.flush()

            self.db_session.add(ListingObservationCategory(
                listing_observation_id=listing_observation_id,
                category_id=category.id
            ))

        self.db_session.flush()

    def _add_country_junctions(self, destination_countries: List[str], listing_observation_id: int) -> None:
        for destination_country in destination_countries:
            self.db_session.merge(Country(
                id=destination_country
            ))
        self.db_session.flush()
        for destination_country in destination_countries:
            self.db_session.add(ListingObservationCountry(
                listing_observation_id=listing_observation_id,
                country_id=destination_country
            ))
        self.db_session.flush()

    def _add_shipping_methods(self, listing_observation_id: int, shipping_descriptions: List[str],
                              shipping_days: List[int],
                              shipping_currencies: List[str], shipping_prices: List[float],
                              shipping_unit_names: List[str], price_is_per_units: List[bool]) -> None:

        for description, days, currency, price, unit_name, price_is_per_unit in zip(shipping_descriptions,
                                                                                    shipping_days, shipping_currencies,
                                                                                    shipping_prices,
                                                                                    shipping_unit_names,
                                                                                    price_is_per_units):
            self.db_session.add(
                ShippingMethod(listing_observation_id=listing_observation_id, description=description,
                               days_shipping_time=days, fiat_currency=currency, price=price,
                               quantity_unit_name=unit_name, price_is_per_unit=price_is_per_unit))

    def _add_bulk_prices(self, listing_observation_id: int, bulk_lower_bounds: List[int],
                         bulk_upper_bounds: List[Union[int, None]],
                         bulk_fiat_prices: List[float], bulk_btc_prices: List[float],
                         bulk_discount_percents: List[float]) -> None:

        for lower_bound, upper_bound, fiat_price, btc_price, discount_percent in zip(
                bulk_lower_bounds, bulk_upper_bounds, bulk_fiat_prices, bulk_btc_prices, bulk_discount_percents):
            self.db_session.add(
                BulkPrice(listing_observation_id=listing_observation_id, unit_amount_lower_bound=lower_bound,
                          unit_amount_upper_bound=upper_bound, unit_fiat_price=fiat_price, unit_btc_price=btc_price,
                          discount_percent=discount_percent))

    def _add_seller_observation_description(self, description_text: str) -> str:
        description_text_hash = hashlib.md5(description_text.encode(MD5_HASH_STRING_ENCODING)).hexdigest()
        existing_seller_description_text = self.db_session.query(SellerDescriptionText).filter_by(
            id=description_text_hash).first()

        if existing_seller_description_text:
            return existing_seller_description_text.id
        else:
            seller_description_text = SellerDescriptionText(
                id=description_text_hash,
                text=description_text
            )
            self.db_session.add(seller_description_text)
            self.db_session.flush()
            return seller_description_text.id

    def _should_scrape_pgp_key_this_session(self, seller: Seller, is_new_seller: bool) -> bool:
        most_recent_pgp_key = self.db_session.query(PGPKey).filter_by(seller_id=seller.id).order_by(
            PGPKey.created_date.desc()).first()

        if is_new_seller:
            return True
        elif most_recent_pgp_key is not None:
            seconds_since_last_pgp_key_scrape = (datetime.utcnow() - most_recent_pgp_key.created_date).total_seconds()
            if seconds_since_last_pgp_key_scrape > RESCRAPE_PGP_KEY_INTERVAL:
                return True

        return False

    def _add_pgp_key(self, seller: Seller, pgp_key_content: str) -> None:
        key_hash: str = hashlib.md5(pgp_key_content.encode(MD5_HASH_STRING_ENCODING)).hexdigest()
        existing_pgp_key = self.db_session.query(PGPKey).filter(PGPKey.seller_id == seller.id,
                                                                PGPKey.key_hash == key_hash)
        if not existing_pgp_key:
            self.db_session.add(PGPKey(seller_id=seller.id, key=pgp_key_content, key_hash=key_hash))
            self.db_session.flush()
        else:
            self.db_session.query(PGPKey).filter(PGPKey.seller_id == seller.id, PGPKey.key_hash == key_hash). \
                update({get_column_name(PGPKey.updated_date): (datetime.utcnow())})

    def print_crawling_debug_message(self, url=None, existing_listing_observation=None) -> None:
        assert (url or existing_listing_observation)
        queue_size = self.queue.qsize()
        parsing_time = time() - self.time_last_received_response
        percent_crawled = round(((self.initial_queue_size - queue_size) / max(1, self.initial_queue_size)) * 100, 2)
        percent_time_spent = round(((ONE_DAY - get_seconds_until_midnight()) / ONE_DAY) * 100, 2)
        progress_msg: str = f"Spent {percent_time_spent}% of this day to crawl {percent_crawled}% of site."

        self.logger.info(f"Last web response was parsed in {parsing_time} seconds.")
        if existing_listing_observation:
            self.logger.info("Database already contains listing with this seller and title for this session.")
            self.logger.info(f"Listing title: {existing_listing_observation.title}")
            self.logger.info("Duplicate listing, skipping...")

        else:
            self.logger.info("Trying to fetch URL: " + url)
        self.logger.info(f"Web session {self.cookie_string}")
        self.logger.info(f"Crawling page nr. {self.initial_queue_size - queue_size} this session.")
        self.logger.info(f"Pages left, approximate: {queue_size}.")
        if percent_crawled >= percent_time_spent:
            self.logger.info(f"{progress_msg}\n")
        else:
            self.logger.warn(f"{progress_msg}\n")

    def _get_logged_in_web_response(self, url_path: str, post_data: dict = None) -> Response:
        url = self._get_schemaed_url_from_path(url_path)
        http_verb = 'POST' if post_data else 'GET'

        response = self._get_web_response_with_error_catch(http_verb, url, proxies=self.proxy,
                                                headers=self.headers, data=post_data)

        if self._is_logged_out(response, self.login_url, self.is_logged_out_phrase):
            self.web_session.cookies.clear()
            self._login_and_set_cookie(response)
            return self._get_logged_in_web_response(url_path)
        else:
            if is_internal_server_error(response):
                raise InternalServerErrorException(response.text)
            elif is_bad_gateway(response):
                raise BadGatewayException(response.text)
            else:
                return response

    def _login_and_set_cookie(self, web_response: Response):

        soup_html = get_page_as_soup_html(web_response.text)
        image_url = self.scraping_funcs.get_captcha_image_url(soup_html)

        image_response = self._get_logged_in_web_response(image_url).content
        base64_image = base64.b64encode(image_response).decode("utf-8")

        time_before_requesting_captcha_solve = time()
        anti_captcha_kwargs = self._get_anti_captcha_kwargs()
        self.logger.info("Sending image to anti-catpcha.com API...")
        captcha_solution_response = ImageToTextTask.ImageToTextTask(
            anticaptcha_key=ANTI_CAPTCHA_ACCOUNT_KEY, **anti_captcha_kwargs
        ).captcha_handler(captcha_base64=base64_image)

        captcha_solution = self._generic_error_catch_wrapper(captcha_solution_response,
                                                             func=lambda d: d["solution"]["text"])

        self.logger.info(f"Captcha solved. Took {time() - time_before_requesting_captcha_solve} seconds.")

        login_payload = self.scraping_funcs.get_login_payload(soup_html, self.username, self.password, captcha_solution)

        web_response = BaseScraper._get_logged_in_web_response(self, self._get_login_url(), post_data=login_payload)

        if self._is_logged_out(web_response, self.login_url, self.is_logged_out_phrase):
            self.logger.warn("INCORRECTLY SOLVED CAPTCHA, TRYING AGAIN...")
            self.anti_captcha_control.complaint_on_result(int(captcha_solution_response["taskId"]), "image")
            self._login_and_set_cookie(web_response)
        else:
            self._add_captcha_solution(base64_image, captcha_solution)
            self._add_web_session_cookie_to_db(self.web_session.cookies)
            self.db_session.commit()
            self.cookie_string = self._get_cookie_string()

    def _add_captcha_solution(self, image: str, solution: str):
        contains_numbers = False
        contains_letters = False
        for l in solution:
            contains_numbers = contains_numbers or l.isdigit()
            contains_letters = contains_letters or l.isalpha()
        assert contains_numbers or contains_letters
        self.db_session.add(
            CaptchaSolution(image=image, solution=solution, market_id=self.market_id, numbers=contains_numbers,
                            letters=contains_letters))

    def _add_web_session_cookie_to_db(self, cookie_jar: RequestsCookieJar) -> None:
        cookie_object_base64 = base64.b64encode(pickle.dumps(dict(cookie_jar))).decode("utf-8")

        existing_cookie: WebSessionCookie = self.db_session.query(WebSessionCookie).filter(
            WebSessionCookie.username == self.username,
            WebSessionCookie.mirror_url == self.mirror_base_url).first()

        if existing_cookie:
            existing_cookie.thread_id = self.thread_id
            existing_cookie.python_object = cookie_object_base64
        else:
            self.db_session.add(
                WebSessionCookie(thread_id=self.thread_id, session_id=self.session_id, username=self.username,
                                 mirror_url=self.mirror_base_url, python_object=cookie_object_base64)
            )

        self.db_session.flush()

    def _get_cookie_from_db(self) -> Union[dict, None]:
        web_session_cookie: WebSessionCookie = self.db_session.query(WebSessionCookie).filter(
            WebSessionCookie.username == self.username,
            WebSessionCookie.mirror_url == self.mirror_base_url).first()

        base64_cookie_dict_binary = web_session_cookie.python_object

        if base64_cookie_dict_binary:
            cookie_dict_binary = base64.b64decode(base64_cookie_dict_binary.encode("utf8"))
            return dict(pickle.loads(cookie_dict_binary))
        else:
            return None

    def _process_generic_error(self, e: BaseException) -> None:
        error_string = get_error_string(self, traceback.format_exc(), sys.exc_info())
        print_error_to_file(self.thread_id, error_string)
        self._log_and_print_error(e, error_string, print_error=False)
        self._wrap_up_session()
        raise e

    def _get_web_response_with_error_catch(self, *args, **kwargs) -> Response:
        while True:
            try:
                web_response = self.web_session.request(*args, **kwargs)
                self.time_last_received_response = time()
                if self._is_meta_refresh(web_response.text):
                    redir_url = self._get_schemaed_url_from_path(self._wait_out_meta_refresh_and_get_redirect_url(web_response))
                    return self.web_session.get(redir_url, headers=self.headers, proxies=self.proxy)
                else:
                    return web_response
            except (KeyboardInterrupt, SystemExit, AttributeError) as e:
                self._log_and_print_error(e, traceback.format_exc())
                self._wrap_up_session()
                raise e
            except (HTTPError, BaseException) as e:
                self._log_and_print_error(e, traceback.format_exc(), print_error=False)
                self.logger.warn(type(e))
                if time() - self.time_last_received_response > DEAD_MIRROR_TIMEOUT:
                    self.mirror_base_url = self._get_new_mirror()

    def _db_error_catch_wrapper(self, *args, func: Callable, error_data: List[Tuple[object, str, datetime]] = None):
        if not error_data:
            error_data = []

        try:
            self.db_session.rollback()
            func(*args)
            self.db_session.commit()
            for error_object, error_string, timestamp in error_data:
                self._log_and_print_error(error_object, error_string, updated_date=timestamp, print_error=False)

        except (SQLAlchemyError, MySQLError, AttributeError, SystemError) as error:
            error_string = traceback.format_exc()
            if type(error) == AttributeError:
                if not error_is_sqlalchemy_error(error_string):
                    self._log_and_print_error(error, error_string)
                    raise error
            error_data.append((error, error_string, datetime.utcnow()))
            seconds_until_next_try = self._get_wait_interval(error_data)
            traceback.print_exc()
            self.logger.info(
                f"Problem with DBMS connection. Retrying in "
                f"{seconds_until_next_try} seconds...")
            sleep(seconds_until_next_try)
            func(*args, func=func, error_data=error_data)

    def _generic_error_catch_wrapper(self, *args, func: Callable) -> any:
        try:
            return func(*args)
        except BaseException as e:
            self._process_generic_error(e)
        except:
            e = GenericException()
            self._process_generic_error(e)

    def _format_logger_message(self, msg: str) -> str:
        return f"[t-ID {self.thread_id}] {msg}"

    def _is_logged_out(self, response: Response, login_url: str, login_page_phrase: str) -> bool:
        if self._has_successful_login_phrase():
            if response.text.find(self._get_successful_login_phrase()) != -1:
                return False
        for history_response in response.history:
            if history_response.is_redirect:
                if history_response.raw.headers._container['location'][1] == login_url:
                    return True

        if response.text.find(login_page_phrase) != -1:
            return True

        return False

    @abstractmethod
    def _get_market_id(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_working_dir(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_headers(self) -> dict:
        pass

    @abstractmethod
    def _get_login_url(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_is_logged_out_phrase(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def populate_queue(self) -> None:
        raise NotImplementedError('')

    @abstractmethod
    def _get_web_session(self) -> requests.Session:
        raise NotImplementedError('')

    @abstractmethod
    def _scrape_queue_item(self, *args) -> None:
        raise NotImplementedError('')

    @abstractmethod
    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        raise NotImplementedError('')

    @abstractmethod
    def _get_anti_captcha_kwargs(self):
        raise NotImplementedError('')

    def _instantiate_web_session(self) -> requests.Session:
        web_session: requests.Session = self._get_web_session()
        cookie_dict_from_db: dict = self._get_cookie_from_db()
        if cookie_dict_from_db:
            web_session.cookies.update(cookie_dict_from_db)
        return web_session

    def _get_schemaed_url_from_path(self, url_path: str, schema: str = "http") -> str:
        return f"{schema}://{self.mirror_base_url}{url_path}"

    @staticmethod
    def _is_meta_refresh(text) -> bool:
        return text[0:512].find('meta http-equiv="refresh"') != -1

    def _wait_out_meta_refresh_and_get_redirect_url(self, web_response: Response) -> str:
        soup_html = get_page_as_soup_html(web_response.text)
        meta_refresh_wait, redirect_url = self.scraping_funcs.get_meta_refresh_interval(soup_html)
        remaining_wait = max(0.0, self.time_last_received_response + meta_refresh_wait - time())
        self.logger.info(f"Waiting remaining {remaining_wait} to circumvent DDoS protection.")
        sleep(remaining_wait)
        return redirect_url

    @abstractmethod
    def _has_successful_login_phrase(self) -> bool:
        raise NotImplementedError('')

    @abstractmethod
    def _get_successful_login_phrase(self) -> str:
        raise NotImplementedError('')

    @staticmethod
    def _is_successful_login_response(response: Response) -> bool:
        return False

    def _get_new_mirror(self) -> str:
        #set failure time for current mirror
        #get mirror with oldest failure time
        #if no mirror with old failure time
            #if db not refreshed last 30 min
                #refresh mirror db
                #recurse
        #test mirror
        #if test failed, recurse
        pass
