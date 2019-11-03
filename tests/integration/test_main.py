import re
from multiprocessing import Queue
from random import shuffle
from typing import List, Tuple
from unittest import TestCase
from unittest.mock import patch, Mock

from requests import Response

import src.main
from definitions import EMPIRE_MARKET_ID, EMPIRE_MARKET_CREDENTIALS, CRYPTONIA_MARKET_CREDENTIALS, \
    CRYPTONIA_MARKET_ID, \
    ROOT_DIR
from src.base_scraper import BaseScraper
from src.base_scraping_manager import ScrapingManager
from src.cryptonia.cryptonia_scrape import CryptoniaScrapingSession
from src.empire.empire_scrape import EmpireScrapingSession
from tests.large_saved_variables import TASK_LIST

TESTS_DIR = ROOT_DIR + "tests/cryptonia/"
HTML_DIR = TESTS_DIR + "html_files/"


def mocked_get_user_input():
    return ((0, None, True), (1, None, True))


class MockedScrapingManager(ScrapingManager):

    def _retrieve_working_mirrors(self, market_id: str) -> List[str]:
        return ["bntee6mf5w2okbpxdxheq7bk36yfmwithltxubliyvum6wlrrxzn72id.onion"]

    def _insert_working_mirrors(self, mirrors: List[str], market_id: str) -> None:
        pass

    def _populate_queue_and_sleep(self, scraping_session: BaseScraper):
        scraping_session.populate_queue()


class MockedCryptoniaScrapingSession(CryptoniaScrapingSession):

    def __init__(self, queue: Queue, username: str, password: str, nr_of_threads: int, thread_id: int, proxy: dict,
             session_id: int, mirror_base_url: str):
        super().__init__(queue, username, password, nr_of_threads, thread_id, proxy, session_id, mirror_base_url=mirror_base_url)

    def populate_queue(self) -> None:
        tasks = TASK_LIST
        shuffle(tasks)
        for task in tasks:
            self.queue.put(task)
        self.initial_queue_size = len(tasks)
    #
    # def _get_logged_in_web_response(self, url_path: str, debug: bool = False) -> str:
    #     file_path = HTML_DIR
    #     if url_path[0:9] == "/products":
    #         file_path += "search_results/saved_cryptonia_search_result_in_category_0"
    #     elif url_path[-11:] == "/2#feedback":
    #         file_path += 'users/saved_cryptonia_user_profile_1'
    #     elif url_path[0:5] == "/user":
    #         file_path += "users/saved_cryptonia_user_profile_0"
    #     elif url_path[0:8] == "/product":
    #         file_path += "listings/saved_cryptonia_listing_8"
    #     else:
    #         raise NotImplementedError('')
    #
    #     with open(file_path) as file:
    #         return file.read()


MOCKED_WEBSITES_TO_BE_SCRAPED: Tuple[Tuple[str], ...] = [
    (EMPIRE_MARKET_ID, EMPIRE_MARKET_CREDENTIALS, EmpireScrapingSession),
    (CRYPTONIA_MARKET_ID, CRYPTONIA_MARKET_CREDENTIALS, MockedCryptoniaScrapingSession)
]


class TestMain(TestCase):

    @patch('src.main.get_user_input', side_effect=mocked_get_user_input)
    @patch('src.main.faulthandler')
    @patch('src.main.get_available_tor_proxies', return_value=list((9050,)))
    @patch('src.main.get_proxies',
           return_value=((), ({'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'},)))
    @patch('src.main.WEBSITES_TO_BE_SCRAPED', MOCKED_WEBSITES_TO_BE_SCRAPED)
    def test_main(self, mocked_get_user_input: Mock, mocked_fault_handler: Mock, mocked_get_available_tor_proxies: Mock,
                  mocked_get_proxies: Mock):
        mocked_fault_handler.return_value = None
        with patch('src.main.ScrapingManager', MockedScrapingManager):
            src.main.run()
