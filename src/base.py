import abc
import hashlib
import sys
import threading
import traceback
from abc import abstractstaticmethod, abstractmethod
from datetime import datetime, timedelta
from multiprocessing import Queue
from time import sleep
from time import time
from typing import List, Union

import cfscrape
import requests
from python3_anticaptcha import AntiCaptchaControl
from sqlalchemy.exc import ProgrammingError
from urllib3.exceptions import HTTPError

from definitions import ANTI_CAPTCHA_ACCOUNT_KEY, MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD, \
    ERROR_FINGER_PRINT_COLUMN_LENGTH, DBMS_DISCONNECT_RETRY_INTERVALS, PYTHON_SIDE_ENCODING
from environmentSettings import DEBUG_MODE, PROXIES
from src.db_utils import _shorten_and_sanitize_for_medium_text_column, get_engine, get_db_session, sanitize_error, \
    get_column_name, get_settings
from src.models.error import Error
from src.models.scraping_session import ScrapingSession
from src.models.settings import Settings
from src.utils import pretty_print_GET, get_error_string, print_error_to_file, is_internal_server_error, \
    InternalServerErrorException, is_bad_gateway, BadGatewayException, queue_is_empty


class BaseFunctions(metaclass=abc.ABCMeta):

    @abstractstaticmethod
    def accepts_currencies(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_title(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_description(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_product_page_urls(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_nr_sold_since_date(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_fiat_currency_and_price(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_cryptocurrency_rates(soup_html):
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_categories_and_ids(soup_html):
        raise NotImplementedError('')


class BaseScraper(metaclass=abc.ABCMeta):

    def __init__(self, queue, username, password, nr_of_threads, thread_id, session_id=None):
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

    def _get_logged_out_web_response(self, url, post_data=None) -> requests.Response:
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

    def _get_logged_in_web_response(self, url, debug=DEBUG_MODE) -> requests.Response:
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
    def _get_web_session(self) -> Union[requests.Session, cfscrape.Session]:
        raise NotImplementedError('')


class BaseScrapingManager(metaclass=abc.ABCMeta):

    def __init__(self, settings: Settings, nr_of_threads: int):
        self.market_credentials = self._get_market_credentials()
        self.market_name = self._get_market_name()
        assert nr_of_threads <= len(self.market_credentials)
        self.queue = Queue()
        self.first_run = True
        self.refill_queue_when_complete = settings.refill_queue_when_complete
        self.nr_of_threads = nr_of_threads

    def run(self, start_immediately: bool) -> None:
        if self.nr_of_threads <= 0:
            return
        if start_immediately:
            self._start_new_session(self.queue, self.nr_of_threads)
        while True:
            self._wait_until_midnight_utc()
            self._update_settings()
            if self._should_start_new_session():
                self._start_new_session(self.queue, self.nr_of_threads)

    def _start_new_session(self, queue: Queue, nr_of_threads) -> None:
        username = self.market_credentials[0][0]
        password = self.market_credentials[0][1]
        scraping_session = self._get_scraping_session(queue, username, password, nr_of_threads, thread_id=0)
        session_id = scraping_session.session_id

        if DEBUG_MODE:
            queue_size = 1000
            db_session = get_db_session(get_engine())
            db_session.query(ScrapingSession).filter(ScrapingSession.id == session_id).update(
                {get_column_name(ScrapingSession.initial_queue_size): queue_size})
            db_session.commit()
            db_session.expunge_all()
            db_session.close()
            for i in range(0, queue_size):
                self.queue.put(str(i))
            sleep(5)
        else:
            scraping_session.populate_queue()
            print("Sleeping 5 seconds to avoid race conditions...")
            sleep(5)

        t = threading.Thread(target=scraping_session.scrape)
        t.start()

        for i in range(1, self.nr_of_threads):
            username = self.market_credentials[i][0]
            password = self.market_credentials[i][1]
            sleep(i * 2)
            scraping_session = self._get_scraping_session(queue, username, password, nr_of_threads, thread_id=i,
                                                          session_id=session_id)
            t = threading.Thread(target=scraping_session.scrape)
            t.start()

        self.first_run = False

    def _should_start_new_session(self) -> bool:
        if self.first_run:
            return True

        if queue_is_empty(self.queue) and self.refill_queue_when_complete:
            return True

        return False

    def _update_settings(self) -> None:
        settings = get_settings(market_name=self.market_name)
        self.refill_queue_when_complete = settings.refill_queue_when_complete

    @staticmethod
    def _wait_until_midnight_utc() -> None:

        utc_current_datetime = datetime.fromtimestamp(datetime.utcnow().timestamp())

        utc_next_day_datetime = utc_current_datetime + timedelta(days=1)

        utc_next_day_date = utc_next_day_datetime.date()

        utc_next_midnight_datetime = datetime(year=utc_next_day_date.year, month=utc_next_day_date.month,
                                              day=utc_next_day_date.day)

        while True:
            seconds_until_midnight = (utc_next_midnight_datetime - datetime.utcnow()).total_seconds()
            if seconds_until_midnight > 0:
                print(f"Waiting until {str(utc_next_midnight_datetime)[:19]} before starting new scraping session.")
                hours = int(seconds_until_midnight // 3600)
                minutes = int((seconds_until_midnight - hours * 3600) // 60)
                seconds = int(seconds_until_midnight - hours * 3600 - minutes * 60)
                print(f"{hours} hours, {minutes} minutes and {seconds} seconds left.\n")
                sleep(min(float(30), seconds_until_midnight))
            else:
                return

    @abstractmethod
    def _get_market_credentials(self) -> List[List[str]]:
        raise NotImplementedError('')

    @abstractmethod
    def _get_scraping_session(self, queue, username, password, nr_of_threads, thread_id,
                              session_id=None) -> BaseScraper:
        raise NotImplementedError('')

    @abstractmethod
    def _get_market_name(self) -> str:
        raise NotImplementedError('')
