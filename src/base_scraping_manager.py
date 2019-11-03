import threading
from multiprocessing import Queue
from time import sleep
from typing import List, Tuple, Type

from definitions import UPDATE_WORKING_MIRRORS_INTERVAL
from src.base_logger import BaseClassWithLogger
from src.base_scraper import BaseScraper
from src.db_utils import get_settings
from src.models.settings import Settings
from src.utils import queue_is_empty, get_seconds_until_midnight, get_utc_datetime_next_midnight


class ScrapingManager(BaseClassWithLogger):

    def __init__(self, settings: Settings, nr_of_threads: int, initial_session_id: int, proxies: Tuple[dict],
                 scraper_class: Type[BaseScraper], market_credentials: Tuple[Tuple[str, str]], market_id: str):
        super().__init__()
        self.market_credentials = market_credentials
        self.market_id = market_id
        self.scraper_class = scraper_class
        assert nr_of_threads <= len(self.market_credentials)
        self.queue = Queue()
        self.first_run = True
        self.refill_queue_when_complete = settings.refill_queue_when_complete
        self.nr_of_threads = nr_of_threads
        self.initial_session_id = initial_session_id
        self.scraping_threads: List[threading.Thread] = []
        self.proxies = proxies

    def run(self, start_immediately: bool) -> None:
        if self.nr_of_threads <= 0:
            return
        if start_immediately:
            self._start_new_session()
        while True:
            self._wait_until_midnight_utc()
            self._update_settings()
            if self._should_start_new_session():
                self._start_new_session()

    def _start_new_session(self) -> None:
        working_mirrors: Tuple[str] = self._retrieve_working_mirrors(self.market_id)
        self._insert_working_mirrors(working_mirrors, self.market_id)
        self.scraping_threads = self._spawn_scraping_threads(self.queue, self.nr_of_threads, working_mirrors)
        maintain_mirrors_daemon_thread = threading.Thread(target=self._maintain_mirrors_daemon, daemon=True)
        maintain_mirrors_daemon_thread.start()

    def _spawn_scraping_threads(self, queue: Queue, nr_of_threads: int, mirrors: Tuple[str]):
        scraping_threads: List[threading.Thread] = []

        username, password, proxy, mirror = self._get_scraping_session_parameters(0, mirrors)
        scraping_session = self.scraper_class(queue, username, password, nr_of_threads, thread_id=0, proxy=proxy,
                                              session_id=self.initial_session_id, mirror_base_url=mirror)
        session_id = scraping_session.session_id

        self._populate_queue_and_sleep(scraping_session)

        t = threading.Thread(target=scraping_session.scrape)
        scraping_threads.append(t)
        t.start()

        for i in range(1, self.nr_of_threads):
            username, password, proxy, mirror = self._get_scraping_session_parameters(i, mirrors)
            sleep(i * 2)
            scraping_session = self.scraper_class(queue, username, password, nr_of_threads, thread_id=i,
                                                  session_id=session_id, proxy=proxy, mirror_base_url=mirror)
            t = threading.Thread(target=scraping_session.scrape)
            scraping_threads.append(t)
            t.start()

        self.first_run = False

    def _should_start_new_session(self) -> bool:
        if self.first_run:
            return True

        if queue_is_empty(self.queue) and self.refill_queue_when_complete:
            return True

        return False

    def _update_settings(self) -> None:
        settings = get_settings(market_name=self.market_id)
        self.refill_queue_when_complete = settings.refill_queue_when_complete

    def _format_logger_message(self, message: str) -> str:
        return f"[RefillQueue {self.refill_queue_when_complete}, ThreadCount {self.nr_of_threads}] {message}"

    def _wait_until_midnight_utc(self) -> None:

        while True:
            utc_next_midnight_datetime = get_utc_datetime_next_midnight()
            seconds_until_midnight = get_seconds_until_midnight(utc_next_midnight_datetime=utc_next_midnight_datetime)
            if seconds_until_midnight and self.queue.empty() > 0:
                self.logger.info(
                    f"Waiting until {str(utc_next_midnight_datetime)[:19]} before starting new scraping session."
                )
                hours = int(seconds_until_midnight // 3600)
                minutes = int((seconds_until_midnight - hours * 3600) // 60)
                seconds = int(seconds_until_midnight - hours * 3600 - minutes * 60)
                self.logger.info(f"{hours} hours, {minutes} minutes and {seconds} seconds left.\n")
                sleep(min(float(30), seconds_until_midnight))
            else:
                return

    def _maintain_mirrors_daemon(self) -> None:
        while True:
            sleep(UPDATE_WORKING_MIRRORS_INTERVAL)
            running_threads = sum([t.is_alive() for t in self.scraping_threads])
            if running_threads == 0 or queue_is_empty(self.queue):
                return
            mirrors = self._retrieve_working_mirrors()
            self._insert_working_mirrors(mirrors)

    def _retrieve_working_mirrors(self, market_id: str) -> List[str]:
        # TODO: retrieve working mirrors from http://darkfailllnkf4vf.onion
        raise NotImplementedError('')

    def _insert_working_mirrors(self, mirrors: Tuple[str], market_id: str) -> None:
        # TODO: abstract method get_mirrors, retrieve working mirrors from http://darkfailllnkf4vf.onion
        raise NotImplementedError('')

    def _get_scraping_session_parameters(self, thread_id: int, mirrors: Tuple[str]) -> Tuple[str, str, dict, str]:
        username = self.market_credentials[thread_id][0]
        password = self.market_credentials[thread_id][1]
        proxy = self.proxies[thread_id % len(self.proxies)]
        mirror = mirrors[thread_id % len(mirrors)]
        return username, password, proxy, mirror

    def _populate_queue_and_sleep(self, scraping_session: BaseScraper) -> None:
        scraping_session.populate_queue()
        print("Sleeping 5 seconds to avoid race conditions...")
        sleep(5)
