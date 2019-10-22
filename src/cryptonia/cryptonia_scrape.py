from random import shuffle
from typing import Union, List, Tuple

import requests

from definitions import CRYPTONIA_MARKET_CATEGORY_INDEX, CRYPTONIA_MARKET_BASE_URL
from src.base import BaseScraper
from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions
import cfscrape

from src.db_utils import get_column_name
from src.models.scraping_session import ScrapingSession
from src.utils import get_page_as_soup_html


class CryptoniaMarketScraper(BaseScraper):

    def __init__(self, queue, username, password, nr_of_threads, thread_id, session_id=None):
        super().__init__(queue, username, password, nr_of_threads, thread_id=thread_id, session_id=session_id)

    def _get_web_session(self) -> requests.Session:
        return cfscrape.Session()

    def populate_queue(self) -> None:
        web_response = self._get_logged_in_web_response(CRYPTONIA_MARKET_CATEGORY_INDEX)
        soup_html = get_page_as_soup_html(self.working_dir, web_response)
        category_lists, category_base_urls = \
            scrapingFunctions.get_category_lists_and_urls(soup_html)
        task_list = []

        for category_list, category_base_url in zip(category_lists, category_base_urls):
            web_response = self._get_logged_in_web_response(f"{CRYPTONIA_MARKET_BASE_URL}/{category_base_url}")
            soup_html = get_page_as_soup_html(self.working_dir, web_response)
            nr_of_pages = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
            task_list.append([category_list, category_base_url])
            for k in range(1, nr_of_pages):
                task_list.append([category_list, f"{category_base_url}/{k+1}"])

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def scrape(self):
        while not self.queue.empty():
            search_result_url = self.queue.get(timeout=1)
            self._generic_error_catch_wrapper(search_result_url, func=self._scrape_items_in_search_result)

        print("Job queue is empty. Wrapping up...")
        self._wrap_up_session()



    def _login_and_set_cookie(self, response=None) -> None:
        pass

    def _get_market_URL(self) -> str:
        pass

    def _get_market_ID(self) -> str:
        pass

    def _get_working_dir(self) -> str:
        pass

    def _get_headers(self) -> dict:
        pass

    def _set_cookies(self) -> None:
        pass

    def _get_login_url(self) -> str:
        pass

    def _get_login_phrase(self) -> str:
        pass
