from typing import Union

import requests

from definitions import CRYPTONIA_MARKET_CATEGORY_INDEX
from src.base import BaseScraper
from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions
import cfscrape

class CryptoniaMarketScraper(BaseScraper):

    def __init__(self, queue, username, password, nr_of_threads, thread_id, session_id=None):
        super().__init__(queue, username, password, nr_of_threads, thread_id=thread_id, session_id=session_id)

    def _get_web_session(self) -> Union[requests.Session, cfscrape.Session]:
        return cfscrape.Session()

    def populate_queue(self) -> None:
        web_response = self._get_logged_in_web_response(CRYPTONIA_MARKET_CATEGORY_INDEX)
        soup_html = self._get_page_as_soup_html(web_response, file="saved_cryptonia_category_index_html")
        list_of_category_list_and_url = \
            scrapingFunctions.get_list_of_cateogory_list_and_url(soup_html)
        task_list = []

        for i in range(0, len(list_of_category_list_and_url)):
            web_response = self._get_logged_in_web_response()
            url = list_of_category_list_and_url[i][0]
            nr_of_pages = nr_of_listings // 15
            for k in range(0, nr_of_pages):
                task_list.append(url + str(k * 15))

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def scrape(self) -> None:
        pass

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
