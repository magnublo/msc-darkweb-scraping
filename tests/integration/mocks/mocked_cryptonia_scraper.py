from multiprocessing import Queue
from random import shuffle

from src.cryptonia.cryptonia_scrape import CryptoniaScrapingSession
from tests.large_saved_variables import TASK_LIST


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