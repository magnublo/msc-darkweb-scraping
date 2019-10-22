import abc
import hashlib
import sys
import traceback
from abc import abstractstaticmethod, abstractmethod
from datetime import datetime
from time import sleep
from time import time

import requests
from bs4 import BeautifulSoup
from python3_anticaptcha import AntiCaptchaControl
from sqlalchemy.exc import ProgrammingError

from definitions import ANTI_CAPTCHA_ACCOUNT_KEY, MAX_NR_OF_ERRORS_STORED_IN_DATABASE_PER_THREAD, \
    ERROR_FINGER_PRINT_COLUMN_LENGTH, DBMS_DISCONNECT_RETRY_INTERVALS
from environmentSettings import DEBUG_MODE, PROXIES
from src.db_utils import _shorten_and_sanitize_for_medium_text_column, get_engine, get_db_session, sanitize_error
from src.models.error import Error
from src.models.scraping_session import ScrapingSession
from src.utils import pretty_print_GET, get_error_string, print_error_to_file


class LoggedOutException(Exception):

    def __init__(self):
        super().__init__("Cookie appears to have been invalidated by remote website.")


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
    def get_origin_country_and_destinations(soup_html):
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
        self.web_session = requests.session()
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

    def _initiate_session(self):
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

    def _log_and_print_error(self, error_object, error_string, updated_date=None, print_error=True):

        if print_error:
            print(error_string)

        errors = self.db_session.query(Error).filter_by(thread_id=self.thread_id).order_by(Error.updated_date.asc())

        if error_object is None:
            error_type = None
        else:
            error_type = type(error_object).__name__

        finger_print = hashlib.md5((error_type + str(time())).encode("utf-8")) \
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

    def _print_exception_triggering_request(self, url):
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

    def _wrap_up_session(self):
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

    def _get_page_response_and_try_forever(self, url, post_data=None):
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

    def _get_page_as_soup_html(self, web_response, file, debug=DEBUG_MODE):
        working_dir = self._get_working_dir()

        if debug:
            saved_html = open(working_dir + file, "r")
            soup_html = BeautifulSoup(saved_html, features="lxml")
            saved_html.close()
            return soup_html
        else:
            return BeautifulSoup(web_response.text, features="lxml")

    def _get_cookie_string(self):
        request_as_string = pretty_print_GET(self.web_session.prepare_request(
            requests.Request('GET', url="http://" + self.headers["Host"], headers=self.headers)))
        lines = request_as_string.split("\n")
        for line in lines:
            if line[0:7].lower() == "cookie:":
                return line.strip().lower()

    def _get_wait_interval(self, error_data):
        nr_of_errors = max(len(error_data)-1, 0)
        highest_index = len(DBMS_DISCONNECT_RETRY_INTERVALS) - 1
        seconds_until_next_try = DBMS_DISCONNECT_RETRY_INTERVALS[
                                     min(nr_of_errors - 1, highest_index)] + self.thread_id * 2
        return seconds_until_next_try

    def print_crawling_debug_message(self, url=None, existing_listing_observation=None):
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


    @abstractmethod
    def _get_web_response(self, url, debug=DEBUG_MODE):
        raise NotImplementedError('')

    @abstractmethod
    def scrape(self):
        raise NotImplementedError('')

    @abstractmethod
    def _login_and_set_cookie(self):
        raise NotImplementedError('')

    @abstractmethod
    def _get_market_URL(self):
        raise NotImplementedError('')

    @abstractmethod
    def _get_market_ID(self):
        raise NotImplementedError('')

    @abstractmethod
    def _get_working_dir(self):
        raise NotImplementedError('')

    @abstractmethod
    def _get_headers(self):
        pass

    @abstractstaticmethod
    def _is_logged_out(response):
        raise NotImplementedError('')

    @abstractmethod
    def _set_cookies(self):
        raise NotImplementedError('')

    @abstractmethod
    def populate_queue(self):
        raise NotImplementedError('')
