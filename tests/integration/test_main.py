from multiprocessing import Queue
from random import shuffle
from typing import List, Tuple
from unittest import TestCase
from unittest.mock import patch, Mock

import src.main
from definitions import EMPIRE_MARKET_ID, CRYPTONIA_MARKET_ID, \
    ROOT_DIR, EMPIRE_MIN_CREDENTIALS_PER_THREAD, CRYPTONIA_MIN_CREDENTIALS_PER_THREAD
from src.base_scraper import BaseScraper
from src.base_scraping_manager import ScrapingManager
from src.cryptonia.cryptonia_scrape import CryptoniaScrapingSession
from src.empire.empire_scrape import EmpireScrapingSession
from tests.large_saved_variables import TASK_LIST

TESTS_DIR = ROOT_DIR + "tests/cryptonia/"
HTML_DIR = TESTS_DIR + "html_files/"


def mocked_get_user_input():
    return ((0, None, True), (1, None, True))

def mocked_get_available_tor_proxies(total_nr_of_threads: int) -> Tuple[int]:
    if total_nr_of_threads != 1:
        raise BaseException
    else:
        return 9050,

class MockedScrapingManager(ScrapingManager):

    def _populate_queue_and_sleep(self, scraping_session: BaseScraper):
        scraping_session.populate_queue()


class MockedCryptoniaScrapingSession(CryptoniaScrapingSession):

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int, proxy: dict,
             session_id: int):
        super().__init__(queue, nr_of_threads, thread_id, proxy, session_id)

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
    (EMPIRE_MARKET_ID, EMPIRE_MIN_CREDENTIALS_PER_THREAD, EmpireScrapingSession),
    (CRYPTONIA_MARKET_ID, CRYPTONIA_MIN_CREDENTIALS_PER_THREAD, MockedCryptoniaScrapingSession)
]


class TestMain(TestCase):

    @patch('src.main.get_user_input', side_effect=mocked_get_user_input)
    @patch('src.main.faulthandler')
    @patch('src.main.get_available_tor_proxies', side_effect=mocked_get_available_tor_proxies)
    @patch('src.main.get_proxies', return_value=((), ({'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'},)))
    @patch('src.main.WEBSITES_TO_BE_SCRAPED', MOCKED_WEBSITES_TO_BE_SCRAPED)
    def test_main(self, mocked_get_user_input: Mock, mocked_fault_handler: Mock, mocked_get_available_tor_proxies: Mock,
                  mocked_get_proxies: Mock):
        mocked_fault_handler.return_value = None
        with patch('src.main.ScrapingManager', MockedScrapingManager):
            src.main.run()
