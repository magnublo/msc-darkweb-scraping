import threading
from abc import abstractmethod
from datetime import datetime, timedelta
from multiprocessing import Queue
from time import sleep
from typing import List

from environment_settings import DEBUG_MODE
from src.base_logger import BaseClassWithLogger
from src.base_scraper import BaseScraper
from src.db_utils import get_db_session, get_engine, get_column_name, get_settings
from src.models.scraping_session import ScrapingSession
from src.models.settings import Settings
from src.utils import queue_is_empty


class BaseScrapingManager(BaseClassWithLogger):

    def __init__(self, settings: Settings, nr_of_threads: int):
        super().__init__()
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