import hashlib
import sys
import traceback
from _mysql_connector import MySQLError
from abc import abstractmethod
from datetime import datetime
from multiprocessing import Queue
from time import sleep
from time import time
from typing import Callable

import requests
from python3_anticaptcha import AntiCaptchaControl
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from urllib3.exceptions import HTTPError

from definitions import ANTI_CAPTCHA_ACCOUNT_KEY, MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD, \
    ERROR_FINGER_PRINT_COLUMN_LENGTH, DBMS_DISCONNECT_RETRY_INTERVALS, PYTHON_SIDE_ENCODING
from environment_settings import DEBUG_MODE, PROXIES
from src.base_logger import BaseClassWithLogger
from src.db_utils import _shorten_and_sanitize_for_medium_text_column, get_engine, get_db_session, sanitize_error
from src.models.error import Error
from src.models.scraping_session import ScrapingSession
from src.utils import pretty_print_GET, get_error_string, print_error_to_file, is_internal_server_error, \
    InternalServerErrorException, is_bad_gateway, BadGatewayException, error_is_sqlalchemy_error, \
    GenericException


class BaseScraper(BaseClassWithLogger):

    def __init__(self, queue: Queue, username: str, password: str, nr_of_threads: int, thread_id: int,
                 session_id: int = None):
        super().__init__()
        engine = get_engine()
        self.login_url = self._get_login_url()
        self.login_phrase = self._get_login_phrase()
        self.working_dir = self._get_working_dir()
        self.logged_out_exceptions = 0
        self.db_session = get_db_session(engine)
        self.username = username
        self.password = password
        self.thread_id = thread_id
        self.nr_of_threads = nr_of_threads
        self.anti_captcha_control = AntiCaptchaControl.AntiCaptchaControl(ANTI_CAPTCHA_ACCOUNT_KEY)
        self.headers = self._get_headers()
        self.queue = queue
        self.market_id = self._get_market_ID()
        self.start_time = time()
        self.duplicates_this_session = 0
        self.web_session = self._get_web_session()
        self.cookie = ""
        self._login_and_set_cookie()
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
                except:
                    print("Thread nr. " + str(self.thread_id) + " has problem querying session id in DB. Retrying...")
                    sleep(5)
        else:
            self.session_id = self._initiate_session()

    def _initiate_session(self) -> int:
        scraping_session = ScrapingSession(
            market=self.market_id,
            duplicates_encountered=self.duplicates_this_session,
            nr_of_threads=self.nr_of_threads
        )
        self.db_session.add(scraping_session)
        self.db_session.commit()
        session_id = scraping_session.id
        print("Thread nr. " + str(self.thread_id) + " initiated scraping_session with ID: " + str(scraping_session.id))
        self.db_session.expunge(scraping_session)
        return session_id

    def _log_and_print_error(self, error_object, error_string, updated_date=None, print_error=True) -> None:

        if print_error:
            print(error_string)

        errors = self.db_session.query(Error).filter_by(thread_id=self.thread_id).order_by(Error.updated_date.asc())

        if error_object is None:
            error_type = None
        else:
            error_type = type(error_object).__name__

        finger_print = hashlib.md5((error_type + str(time())).encode(PYTHON_SIDE_ENCODING)) \
                           .hexdigest()[0:ERROR_FINGER_PRINT_COLUMN_LENGTH]

        error_string = sanitize_error(error_string, locals().keys())
        error_string = _shorten_and_sanitize_for_medium_text_column(error_string)

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

    def _get_logged_out_web_response(self, url: str, post_data: dict = None) -> requests.Response:
        tries = 0

        while True:
            print(time())
            print("Thread nr. " + str(self.thread_id) + ' trying to retrieve page ' + url + "...")
            print("Try nr. " + str(tries))
            try:
                if post_data:
                    response = self.web_session.post(url, data=post_data, proxies=PROXIES, headers=self.headers)
                else:
                    response = self.web_session.get(url, proxies=PROXIES, headers=self.headers)
                return response
            except:
                tries += 1

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

    def print_crawling_debug_message(self, url=None, existing_listing_observation=None) -> None:
        assert (url or existing_listing_observation)
        queue_size = self.queue.qsize()
        parsing_time = time() - self.time_last_received_response
        print(datetime.fromtimestamp(time()))
        print(f"Last web response was parsed in {parsing_time} seconds.")
        if existing_listing_observation:
            print("Database already contains listing with this seller and title for this session.")
            print(f"Listing title: {existing_listing_observation.title}")
            print("Duplicate listing, skipping...")

        else:
            print("Trying to fetch URL: " + url)
        print(f"Thread nr. {self.thread_id}")
        print(f"Web session {self.cookie}")
        print(f"Crawling page nr. {self.initial_queue_size - queue_size} this session.")
        print(f"Pages left, approximate: {queue_size}.")
        print("\n")

    def _get_logged_in_web_response(self, url: str, debug: bool = DEBUG_MODE) -> requests.Response:
        while True:
            try:
                if debug:
                    self.time_last_received_response = time()
                    return None
                else:
                    response = self.web_session.get(url, proxies=PROXIES, headers=self.headers)

                    tries = 0

                    while tries < 5:
                        if self._is_logged_out(response, self.login_url, self.login_phrase):
                            tries += 1
                            response = self.web_session.get(url, proxies=PROXIES, headers=self.headers)
                        else:
                            if is_internal_server_error(response):
                                raise InternalServerErrorException(response.text)
                            elif is_bad_gateway(response):
                                raise BadGatewayException(response.text)
                            else:
                                self.time_last_received_response = time()
                                return response

                    self._login_and_set_cookie(response)
                    return self._get_logged_in_web_response(url)
            except (KeyboardInterrupt, SystemExit, AttributeError) as e:
                self._log_and_print_error(e, traceback.format_exc())
                self._wrap_up_session()
                raise e

            except (HTTPError, BaseException) as e:
                self._log_and_print_error(e, traceback.format_exc())

    def _process_generic_error(self, e: BaseException) -> None:
        error_string = get_error_string(self, traceback.format_exc(), sys.exc_info())
        print_error_to_file(self.thread_id, error_string)
        self._log_and_print_error(e, error_string, print_error=False)
        self._wrap_up_session()
        raise e

    def _db_error_catch_wrapper(self, *args, func, error_data=None):
        if not error_data:
            error_data = []

        if not error_data:
            error_data = []

        try:
            self.db_session.rollback()
            func(*args)
            self.db_session.commit()
            for entry in error_data:
                self._log_and_print_error(entry[0], entry[1], updated_date=entry[2], print_error=False)
            error_data = []
        except (SQLAlchemyError, MySQLError, AttributeError, SystemError) as error:
            error_string = traceback.format_exc()
            if type(error) == AttributeError:
                if not error_is_sqlalchemy_error(error_string):
                    self._log_and_print_error(error, error_string)
                    raise error
            error_data.append([error, error_string, datetime.utcnow()])
            seconds_until_next_try = self._get_wait_interval(error_data)
            traceback.print_exc()
            print(
                f"Thread {self.thread_id} has problem with DBMS connection. Retrying in "
                f"{seconds_until_next_try} seconds...")
            sleep(seconds_until_next_try)
            func(*args, func=func, error_data=error_data)

    def _generic_error_catch_wrapper(self, *args, func: Callable):
        try:
            func(*args)
        except BaseException as e:
            self._process_generic_error(e)
        except:
            e = GenericException()
            self._process_generic_error(e)

    @staticmethod
    def _is_logged_out(response, login_url, login_page_phrase) -> bool:
        for history_response in response.history:
            if history_response.is_redirect:
                if history_response.raw.headers._container['location'][1] == login_url:
                    return True

        if response.text.find(login_page_phrase) != -1:
            return True

        return False

    @abstractmethod
    def scrape(self) -> None:
        raise NotImplementedError('')

    @abstractmethod
    def _login_and_set_cookie(self, response=None) -> None:
        raise NotImplementedError('')

    @abstractmethod
    def _get_market_URL(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_market_ID(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_working_dir(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_headers(self) -> dict:
        pass

    @abstractmethod
    def _set_cookies(self) -> None:
        raise NotImplementedError('')

    @abstractmethod
    def _get_login_url(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def _get_login_phrase(self) -> str:
        raise NotImplementedError('')

    @abstractmethod
    def populate_queue(self) -> None:
        raise NotImplementedError('')

    @abstractmethod
    def _get_web_session(self) -> requests.Session:
        raise NotImplementedError('')
