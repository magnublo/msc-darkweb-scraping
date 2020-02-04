import threading
from multiprocessing import Queue
from time import sleep
from typing import List, Tuple, Type, Dict

from sqlalchemy.orm import Session

from definitions import ONE_HOUR
from src.base.base_logger import BaseClassWithLogger
from src.base.base_scraper import BaseScraper
from src.db_utils import get_settings, get_engine, get_db_session
from src.models.settings import Settings
from src.utils import queue_is_empty, get_seconds_until_midnight, get_utc_datetime_next_midnight


class ScrapingManager(BaseClassWithLogger):

    def __init__(self, settings: Settings, nr_of_threads: int, initial_session_id: int, proxies: Tuple[dict],
                 scraper_class: Type[BaseScraper], market_id: str):
        super().__init__()
        self.market_id = market_id
        self.scraper_class = scraper_class
        self.queue = Queue()
        self.first_run = True
        self.refill_queue_when_complete = settings.refill_queue_when_complete
        self.nr_of_threads = nr_of_threads
        self.initial_session_id = initial_session_id
        self.scraping_threads: List[threading.Thread] = []
        self.proxies = proxies
        self.shared_db_session: Session = get_db_session(get_engine())

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
        self._spawn_scraping_threads(self.queue, self.shared_db_session, self.nr_of_threads)

    def _spawn_scraping_threads(self, queue: Queue, shared_db_session: Session, nr_of_threads: int):
        scraping_threads: List[threading.Thread] = []

        proxy = self._get_scraping_session_parameters(0)
        scraping_session = self.scraper_class(queue, nr_of_threads, thread_id=0, proxy=proxy,
                                              session_id=self.initial_session_id, shared_db_session=shared_db_session)
        session_id = scraping_session.session_id

        self._populate_queue_and_sleep(scraping_session)

        t = threading.Thread(target=scraping_session.scrape)
        scraping_threads.append(t)
        t.start()

        for i in range(1, self.nr_of_threads):
            proxy = self._get_scraping_session_parameters(i)
            sleep(1)
            scraping_session = self.scraper_class(queue, nr_of_threads, thread_id=i,
                                                  session_id=session_id, proxy=proxy, shared_db_session=shared_db_session)
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
        output_frequency: float = 6*ONE_HOUR
        is_midnight: bool = False
        while True:
            utc_next_midnight_datetime = get_utc_datetime_next_midnight()
            seconds_until_midnight = get_seconds_until_midnight(utc_next_midnight_datetime=utc_next_midnight_datetime)
            if not is_midnight and self.queue.empty():
                self.logger.info(
                    f"Waiting until {str(utc_next_midnight_datetime)[:19]} before starting new scraping session."
                )
                hours = int(seconds_until_midnight // 3600)
                minutes = int((seconds_until_midnight - hours * 3600) // 60)
                seconds = int(seconds_until_midnight - hours * 3600 - minutes * 60)
                self.logger.info(f"{hours} hours, {minutes} minutes and {seconds} seconds left.\n")
                if output_frequency >= seconds_until_midnight:
                    is_midnight = True
                sleep(min(output_frequency, seconds_until_midnight))
            else:
                return

    def _get_scraping_session_parameters(self, thread_id: int) -> Dict[str, str]:
        proxy = self.proxies[thread_id % len(self.proxies)]
        return proxy

    def _populate_queue_and_sleep(self, scraping_session: BaseScraper) -> None:
        scraping_session.populate_queue()
