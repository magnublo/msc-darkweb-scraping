import abc
import time
from abc import abstractstaticmethod, abstractmethod

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from definitions import DB_ENGINE_URL, DB_CLIENT_ENCODING, PROXIES, DEBUG_MODE
engine = create_engine(DB_ENGINE_URL, encoding=DB_CLIENT_ENCODING)
Session = sessionmaker(bind=engine)
Base = declarative_base()
db_session = Session()

from src.models.scraping_session import ScrapingSession


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

    def __init__(self):
        self.cookies = self._login_and_set_cookie()
        self.headers = self._get_headers()
        self.market_id = self._get_market_ID()
        self.start_time = time.time()

        self.session = ScrapingSession(
            time_started=self.start_time,
            market=self.market_id
        )

        db_session.add(self.session)
        db_session.flush()
        self.duplicates_this_session = 0

        self.session_id = self.session.id

    def _get_page_as_soup_html(self, url, file, debug=DEBUG_MODE):
        working_dir = self._get_working_dir()

        if debug:
            saved_html = open(working_dir + file, "r")
            soup_html = BeautifulSoup(saved_html)
            saved_html.close()
            return soup_html
        else:
            response = requests.get(url, proxies=PROXIES, headers=self.headers)
            if self._is_logged_out(response):
                self._handle_logged_out_session()
                return self._get_page_as_soup_html(url, file)
            return BeautifulSoup(response.text)

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
    def _handle_logged_out_session(self):
        raise NotImplementedError('')
