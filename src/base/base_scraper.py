import base64
import hashlib
import pickle
import sys
import traceback
from abc import abstractmethod
from datetime import datetime
from multiprocessing import Queue
from threading import RLock
from time import sleep
from time import time
from typing import Callable, List, Tuple, Union, Type, Any, Dict, Optional

import requests
from python3_anticaptcha import AntiCaptchaControl, ImageToTextTask
from requests import Response
from requests.cookies import RequestsCookieJar
from sqlalchemy.exc import ProgrammingError

from definitions import ANTI_CAPTCHA_ACCOUNT_KEY, MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD, \
    ERROR_FINGER_PRINT_COLUMN_LENGTH, DBMS_DISCONNECT_RETRY_INTERVALS, ONE_DAY, \
    RESCRAPE_PGP_KEY_INTERVAL, MD5_HASH_STRING_ENCODING, DEAD_MIRROR_TIMEOUT, WEB_EXCEPTIONS_TUPLE, \
    DB_EXCEPTIONS_TUPLE
from src.base.base_functions import BaseFunctions
from src.base.base_logger import BaseClassWithLogger
from src.db_utils import shorten_and_sanitize_for_medium_text_column, get_engine, get_db_session, sanitize_error, \
    get_column_name
from src.mirror_manager import MirrorManager
from src.models.bulk_price import BulkPrice
from src.models.captcha_solution import CaptchaSolution
from src.models.country import Country
from src.models.country_alias import CountryAlias
from src.models.description_text import DescriptionText
from src.models.error import Error
from src.models.listing_category import ListingCategory
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory
from src.models.listing_observation_country import ListingObservationCountry
from src.models.pgp_key import PGPKey
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.shipping_method import ShippingMethod
from src.models.user_credential import UserCredential
from src.models.web_session_cookie import WebSessionCookie
from src.utils import pretty_print_GET, get_error_string, print_error_to_file, error_is_sqlalchemy_error, \
    GenericException, get_seconds_until_midnight, get_page_as_soup_html, get_proxy_port, get_schemaed_url, \
    temporary_server_error, pretty_print_POST, determine_real_country


class BaseScraper(BaseClassWithLogger):

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int,
                 proxy: dict, session_id: int):
        super().__init__()
        engine = get_engine()
        self.pages_counter = 0
        self.mirror_db_lock: RLock = self._get_mirror_db_lock()
        self.user_credentials_db_lock: RLock = self._get_user_credentials_db_lock()
        self.proxy_port: int = get_proxy_port(proxy)
        self.time_last_refreshed_mirror_db = 0.0
        self.scraping_funcs = self._get_scraping_funcs()
        self.login_url = self._get_login_url()
        self.is_logged_out_phrase = self._get_is_logged_out_phrase()
        self.working_dir = self._get_working_dir()
        self.proxy = proxy
        self.db_session = get_db_session(engine)
        self.thread_id = thread_id
        self.nr_of_threads = nr_of_threads
        self.anti_captcha_control = AntiCaptchaControl.AntiCaptchaControl(ANTI_CAPTCHA_ACCOUNT_KEY)
        self.queue = queue
        self.market_id = self._get_market_id()
        self.start_time = time()
        self.duplicates_this_session = 0
        self.web_sessions: Tuple[requests.Session] = self._get_web_sessions()
        self.initial_queue_size = self.queue.qsize()
        self.time_last_received_response = time()
        self.session_id = session_id or self._initiate_session()
        self.mirror_manager = MirrorManager(self)
        self.mirror_base_url: str = self.mirror_manager.get_new_mirror()
        self.headers = self._get_headers()
        self._set_saved_cookie_on_web_sessions()
        self.web_session = self._rotate_web_session()

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

        finger_print = hashlib.md5((error_type + str(time())).encode(MD5_HASH_STRING_ENCODING)).hexdigest()[
                       0:ERROR_FINGER_PRINT_COLUMN_LENGTH]

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
            print_error_to_file(self.market_id, self.thread_id, meta_error_string, "meta")
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
            except DB_EXCEPTIONS_TUPLE:
                sleep(10)

        self.db_session.expunge_all()
        self.db_session.close()

    def _get_cookie_string(self, web_session: requests.Session) -> str:
        request_as_string = pretty_print_GET(web_session.prepare_request(
            requests.Request('GET', self._get_schemaed_url_from_path("/"), headers=self.headers)))
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
            if existing_listing_observation.origin_country is None:
                return existing_listing_observation, True  # This listing is the result of an exception and rollback
                # mid-scrape
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
        existing_seller_observation = self.db_session.query(SellerObservation.id) \
            .filter(SellerObservation.session_id == self.session_id) \
            .join(Seller) \
            .filter(SellerObservation.seller_id == seller_id) \
            .first()

        if existing_seller_observation:
            return False
        else:
            return True

    def _add_category_junctions(self, listing_observation_id: int, listing_categories: Tuple[
        Tuple[str, Optional[int], Optional[str], Optional[int]]]) -> None:

        for category_name, marketside_category_id, parent_category_name, category_level in listing_categories:
            category: ListingCategory = self.db_session.query(ListingCategory).filter(
                ListingCategory.website_id == marketside_category_id,
                ListingCategory.name == category_name,
                ListingCategory.market == self.market_id).first()

            parent_category = self.db_session.query(ListingCategory.id).filter(
                ListingCategory.name == parent_category_name, ListingCategory.market == self.market_id,
                ListingCategory.level == category_level - 1).first()  # TODO: Move inside 'if' when db is cleaned

            if not category:
                category = ListingCategory(
                    website_id=marketside_category_id,
                    name=category_name,
                    market=self.market_id,
                    parent_category_id=parent_category.id if parent_category else None,
                    level=category_level
                )
                self.db_session.add(category)
                self.db_session.flush()
            else:
                # TODO: Temporary. can be removed when db is updated
                category.website_id = marketside_category_id
                category.name = category_name
                category.parent_category = parent_category.id if parent_category else None
                category.level = category_level
                self.db_session.flush()

            self.db_session.add(ListingObservationCategory(
                listing_observation_id=listing_observation_id,
                category_id=category.id
            ))

        self.db_session.flush()

    def _add_country_junctions(self, destination_country_ids: Tuple[int], listing_observation_id: int) -> None:
        for country_id in destination_country_ids:
            self.db_session.add(ListingObservationCountry(
                listing_observation_id=listing_observation_id,
                country_id=country_id
            ))
        self.db_session.flush()

    def _add_countries(self, *countries: str) -> Tuple[int]:
        country_ids: List[int] = []
        for country_name in countries:
            # first, check if alias is stored and match with country
            existing_country = self.db_session.query(Country.id).filter(
                Country.id == self.db_session.query(CountryAlias.country_id).filter(
                    CountryAlias.name == country_name).subquery()).first()
            if existing_country:
                country_ids.append(existing_country.id)
            else:
                # country alias not found. first checking with debian db or stored continent dict
                legit_country_name, alpha_2, alpha_3, is_continent = determine_real_country(country_name)
                # whatever name we get back from the 'determine_real_country' function, we either query it or create it
                db_country_id: int = self._create_or_fetch_country(legit_country_name, alpha_2, alpha_3, is_continent)
                # adding missing alias for this country
                self.db_session.add(CountryAlias(name=country_name, country_id=db_country_id))
                self.db_session.flush()
                country_ids.append(db_country_id)

        assert len(country_ids) == len(countries)
        return tuple(country_ids)

    def _add_shipping_methods(self, listing_observation_id: int, shipping_methods: Tuple[
        Tuple[str, Optional[int], str, float, Optional[str], Optional[bool]]]) -> None:

        for description, days, currency, price, unit_name, price_is_per_unit in shipping_methods:
            self.db_session.add(
                ShippingMethod(listing_observation_id=listing_observation_id, description=description,
                               days_shipping_time=days, fiat_currency=currency, price=price,
                               quantity_unit_name=unit_name, price_is_per_unit=price_is_per_unit))

    def _add_bulk_prices(self, listing_observation_id: int,
                         bulk_prices: Tuple[Tuple[int, Optional[int], float, float, Optional[float]]]) -> None:

        for lower_bound, upper_bound, fiat_price, btc_price, discount_percent in bulk_prices:
            self.db_session.add(
                BulkPrice(listing_observation_id=listing_observation_id, unit_amount_lower_bound=lower_bound,
                          unit_amount_upper_bound=upper_bound, unit_fiat_price=fiat_price, unit_btc_price=btc_price,
                          discount_percent=discount_percent))

    def _add_text(self, text: Optional[str]) -> int:
        text = text if text else ""
        text_hash = hashlib.md5(text.encode(MD5_HASH_STRING_ENCODING)).hexdigest()
        text_id_result = self.db_session.query(DescriptionText.id).filter(
            DescriptionText.text_hash == text_hash).first()

        if text_id_result:
            return text_id_result.id
        else:
            new_text = DescriptionText(text_hash=text_hash, text=text)
            self.db_session.add(new_text)
            self.db_session.flush()
            return new_text.id

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
        existing_pgp_key = self.db_session.query(PGPKey.id).filter(PGPKey.seller_id == seller.id,
                                                                   PGPKey.key_hash == key_hash).first()
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
        self.logger.info(f"Crawling page nr. {self.initial_queue_size - queue_size} this session.")
        self.logger.info(f"Pages left, approximate: {queue_size}.")
        if percent_crawled >= percent_time_spent:
            self.logger.info(f"{progress_msg}\n")
        else:
            self.logger.warn(f"{progress_msg}\n")

    def _get_logged_in_web_response(self, url_path: str, post_data: dict = None,
                                    web_session: requests.Session = None) -> Response:
        web_session = web_session if web_session else self.web_session
        url = self._get_schemaed_url_from_path(url_path)
        http_verb = 'POST' if post_data else 'GET'

        response = self._get_web_response_with_error_catch(web_session, http_verb, url, proxies=self.proxy,
                                                           headers=self.headers, data=post_data)

        if self._is_logged_out(response, self.login_url, self.is_logged_out_phrase) and not post_data:
            self._login_and_set_cookie(web_session, response)
            return self._get_logged_in_web_response(url_path, web_session=web_session)
        else:
            self.pages_counter += 1
            if not post_data:
                web_session.headers.update({"Origin": self._get_schemaed_url_from_path(url_path)})
            self.web_session = self._rotate_web_session()
            return response

    def _login_and_set_cookie(self, web_session: requests.Session, web_response: Response):
        soup_html = get_page_as_soup_html(web_response.text)
        image_url = self.scraping_funcs.get_captcha_image_url_from_market_page(soup_html)
        image_response = self._get_logged_in_web_response(image_url, web_session=web_session).content
        base64_image = base64.b64encode(image_response).decode("utf-8")
        captcha_solution, captcha_solution_response = self._get_captcha_solution_from_base64_image(
            base64_image)

        login_payload = self.scraping_funcs.get_login_payload(soup_html, self.web_session.username,
                                                              self.web_session.password, captcha_solution)

        web_response = self._get_logged_in_web_response(self._get_login_url(), post_data=login_payload,
                                                        web_session=web_session)

        if self._is_logged_out(web_response, self.login_url, self.is_logged_out_phrase):
            self.logger.warn("INCORRECTLY SOLVED CAPTCHA, TRYING AGAIN...")
            self.anti_captcha_control.complaint_on_result(int(captcha_solution_response["taskId"]), "image")
            self._add_captcha_solution(base64_image, captcha_solution, correct=False)
            self._login_and_set_cookie(web_session, web_response)
        else:
            web_session.finger_print = hashlib.md5(
                self._get_cookie_string(web_session).encode(MD5_HASH_STRING_ENCODING)).hexdigest()[0:3]
            self._add_captcha_solution(base64_image, captcha_solution, correct=True)
            self._add_web_session_cookie_to_db(self.web_session.cookies)
            self.db_session.commit()

    def _add_captcha_solution(self, image: str, solution: str, correct: bool, website: str = None):
        website = website if website else self.market_id
        contains_numbers = False
        contains_letters = False
        for l in solution:
            contains_numbers = contains_numbers or l.isdigit()
            contains_letters = contains_letters or l.isalpha()
        assert contains_numbers or contains_letters
        self.db_session.add(
            CaptchaSolution(image=image, solution=solution, website=website, numbers=contains_numbers,
                            letters=contains_letters, solved_correctly=correct))

    def _add_web_session_cookie_to_db(self, cookie_jar: RequestsCookieJar) -> None:
        cookie_object_base64 = base64.b64encode(pickle.dumps(dict(cookie_jar))).decode("utf-8")
        username = self.web_session.username

        existing_cookie: WebSessionCookie = self.db_session.query(WebSessionCookie).filter(
            WebSessionCookie.username == username,
            WebSessionCookie.mirror_url == self.mirror_base_url).first()

        if existing_cookie:
            existing_cookie.thread_id = self.thread_id
            existing_cookie.python_object = cookie_object_base64
        else:
            self.db_session.add(
                WebSessionCookie(thread_id=self.thread_id, session_id=self.session_id, username=username,
                                 mirror_url=self.mirror_base_url, python_object=cookie_object_base64)
            )
        self.logger.info(
            "Saved cookie {0} to db for username {1} and url {2}".format(''.join(str(dict(cookie_jar)).split('\n')),
                                                                         username, f"{self.mirror_base_url[0:5]}..."))
        self.db_session.commit()

    def _set_saved_cookie_on_web_sessions(self) -> None:
        for web_session in self.web_sessions:
            cookie_dict_from_db: dict = self._get_cookie_from_db(web_session.username)
            if cookie_dict_from_db:
                self.logger.info(
                    "Loaded cookie {0} from db for user {1]".format(''.join(str(cookie_dict_from_db).split('\n')),
                                                                    web_session.username))
                web_session.cookies.update(cookie_dict_from_db)
                web_session.finger_print = hashlib.md5(
                    self._get_cookie_string(web_session).encode(MD5_HASH_STRING_ENCODING)).hexdigest()[0:3]
            else:
                self.logger.info(f"Found no stored cookie for user {web_session.username}.")
                web_session.finger_print = ""

    def _get_cookie_from_db(self, username: str) -> Union[dict, None]:
        web_session_cookie: WebSessionCookie = self.db_session.query(WebSessionCookie).filter(
            WebSessionCookie.username == username,
            WebSessionCookie.mirror_url == self.mirror_base_url).first()

        if web_session_cookie:
            base64_cookie_dict_binary = web_session_cookie.python_object
            cookie_dict_binary = base64.b64decode(base64_cookie_dict_binary.encode("utf8"))
            return dict(pickle.loads(cookie_dict_binary))
        else:
            return None

    def _process_generic_error(self, e: BaseException) -> None:
        error_string = get_error_string(self, traceback.format_exc(), sys.exc_info())
        print_error_to_file(self.market_id, self.thread_id, error_string)
        self._log_and_print_error(e, error_string, print_error=False)
        self._wrap_up_session()
        raise e

    def _get_web_response_with_error_catch(self, web_session, http_verb, url, *args, **kwargs) -> Response:
        while True:
            self._log_web_request(web_session, http_verb, url, *args, **kwargs)
            try:
                web_response = web_session.request(http_verb, url, *args, **kwargs)
                if temporary_server_error(web_response):
                    raise temporary_server_error(web_response)
                self.time_last_received_response = time()
                if self._is_meta_refresh(web_response.text):
                    redir_url = self._get_schemaed_url_from_path(
                        self._wait_out_meta_refresh_and_get_redirect_url(web_response))
                    return self._get_web_response_with_error_catch(web_session, 'GET', redir_url, headers=self.headers,
                                                                   proxies=self.proxy)
                else:
                    return web_response
            except (KeyboardInterrupt, SystemExit, AttributeError) as e:
                self._log_and_print_error(e, traceback.format_exc())
                self._wrap_up_session()
                raise e
            except WEB_EXCEPTIONS_TUPLE as e:
                self._log_and_print_error(e, traceback.format_exc(), print_error=False)
                self.logger.warn(type(e).__name__)
                if time() - self.time_last_received_response > DEAD_MIRROR_TIMEOUT:
                    self.mirror_base_url = self._db_error_catch_wrapper(func=self.mirror_manager.get_new_mirror,
                                                                        rollback=False)
                    self.headers = self._get_headers()

    def _db_error_catch_wrapper(self, *args, func: Callable, error_data: List[Tuple[object, str, datetime]] = None,
                                rollback: bool = True) -> Any:
        if not error_data:
            error_data = []

        try:
            if rollback:
                self.db_session.rollback()
            res = func(*args)
            self.db_session.commit()
            for error_object, error_string, timestamp in error_data:
                self._log_and_print_error(error_object, error_string, updated_date=timestamp, print_error=False)
            return res

        except DB_EXCEPTIONS_TUPLE as error:
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
            return self._db_error_catch_wrapper(*args, func=func, error_data=error_data, rollback=rollback)

    def _generic_error_catch_wrapper(self, *args, func: Callable) -> any:

        try:
            return func(*args)
        except BaseException as e:
            self._process_generic_error(e)
        # noinspection PyBroadException
        except:
            e = GenericException()
            self._process_generic_error(e)

    def _format_logger_message(self, msg: str) -> str:
        if hasattr(self, 'web_session'):
            return f"[t-ID {self.thread_id} prx {self.proxy_port} wbs {str(self.web_session.__hash__())[-3:]}] {msg}"
        else:
            return f"[t-ID {self.thread_id} prx {self.proxy_port}] {msg}"

    def _is_logged_out(self, response: Response, login_url: str, login_page_phrase: str) -> bool:
        if self._has_successful_login_phrase():
            if response.text.find(self._get_successful_login_phrase()) != -1:
                return False
        for history_response in response.history:
            if history_response.is_redirect:
                if history_response.headers.get('location') == login_url:
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
    def _get_web_session_object(self) -> requests.Session:
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

    def _get_schemaed_url_from_path(self, url_path: str) -> str:
        return f"{get_schemaed_url(self.mirror_base_url, schema='http')}{url_path}"

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

    @abstractmethod
    def _get_min_credentials_per_thread(self) -> int:
        raise NotImplementedError('')

    @staticmethod
    def _is_successful_login_response(response: Response) -> bool:
        return False

    @abstractmethod
    def _get_mirror_db_lock(self) -> RLock:
        raise NotImplementedError('')

    @abstractmethod
    def _get_user_credentials_db_lock(self) -> RLock:
        raise NotImplementedError('')

    def _get_captcha_solution_from_base64_image(self, base64_image: str, anti_captcha_kwargs: Dict[str, int] = None) \
            -> Tuple[str, dict]:
        time_before_requesting_captcha_solve = time()
        anti_captcha_kwargs = anti_captcha_kwargs if anti_captcha_kwargs else self._get_anti_captcha_kwargs()
        self.logger.info("Sending image to anti-catpcha.com API...")
        captcha_solution_response = ImageToTextTask.ImageToTextTask(
            anticaptcha_key=ANTI_CAPTCHA_ACCOUNT_KEY, **anti_captcha_kwargs
        ).captcha_handler(captcha_base64=base64_image)

        captcha_solution = self._generic_error_catch_wrapper(captcha_solution_response,
                                                             func=lambda d: d["solution"]["text"])

        self.logger.info(f"Captcha solved. Took {time() - time_before_requesting_captcha_solve} seconds.")

        return captcha_solution, captcha_solution_response

    def _get_web_session(self) -> requests.Session:
        with self.user_credentials_db_lock:
            web_session: requests.Session = self._get_web_session_object()

            user_credential: UserCredential = self.db_session.query(UserCredential).filter(
                UserCredential.market_id == self.market_id, UserCredential.thread_id == -1,
                UserCredential.is_registered == 1).join(WebSessionCookie,
                                                        WebSessionCookie.username == UserCredential.username,
                                                        isouter=True).order_by(
                WebSessionCookie.updated_date.desc()).first()

            assert user_credential is not None
            assert user_credential.thread_id == -1
            user_credential.thread_id = self.thread_id
            web_session.username = user_credential.username
            web_session.password = user_credential.password
            self.logger.info(f"Loaded username {user_credential.username}")
            self.db_session.commit()
            return web_session

    def _get_web_sessions(self) -> Tuple[requests.Session]:
        nr_of_web_sessions = self._get_min_credentials_per_thread()
        web_sessions: List[requests.Session] = []
        for _ in range(nr_of_web_sessions):
            web_sessions.append(self._get_web_session())
        return tuple(web_sessions)

    def _rotate_web_session(self) -> requests.Session:
        return self.web_sessions[self.pages_counter % len(self.web_sessions)]

    def _log_web_request(self, session, verb, *args, **kwargs) -> None:
        kwargs.pop('proxies')
        if verb is 'GET':
            req_str = pretty_print_GET(session.prepare_request(requests.Request(verb, *args, **kwargs)))
        elif verb is 'POST':
            req_str = pretty_print_POST(session.prepare_request(requests.Request(verb, *args, **kwargs)))
        else:
            raise AssertionError(f'Unconfigured verb {verb}')
        self.logger.debug(req_str)

    def _create_or_fetch_country(self, legit_country_name: str, alpha_2: str, alpha_3: str, is_continent: bool) -> int:
        country: Country = self.db_session.query(Country).filter(Country.name == legit_country_name).first()
        if not country:
            country = Country(name=legit_country_name, iso_alpha2_code=alpha_2, iso_alpha3_code=alpha_3,
                              is_continent=is_continent)
            self.db_session.add(country)
            self.db_session.flush()
        return country.id
