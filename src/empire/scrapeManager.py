import threading
import datetime
from multiprocessing import Queue
from time import sleep, time

from definitions import EMPIRE_MARKET_CREDENTIALS
from environmentSettings import DEBUG_MODE
from src.db_utils import get_settings, get_engine, get_db_session, get_column_name
from src.empire.scrape import EmpireScrapingSession
from src.models.scraping_session import ScrapingSession


def queue_is_empty(queue):
    is_empty = queue.empty()
    sleep(100)  # Must be sure that queue is indeed empty.
    return queue.empty() and is_empty


class EmpireScrapingManager:

    def __init__(self, settings, nr_of_threads=1):
        assert nr_of_threads <= len(EMPIRE_MARKET_CREDENTIALS)
        self.queue = Queue()
        self.first_run = True
        self.refill_queue_when_complete = settings.refill_queue_when_complete
        self.nr_of_threads = nr_of_threads

    def run(self) -> None:
        while True:
            self._wait_until_midnight_utc()
            self._update_settings()
            if self._should_start_new_session():
                self._start_new_session(self.queue, self.nr_of_threads)

    def _start_new_session(self, queue, nr_of_threads) -> None:
        username = EMPIRE_MARKET_CREDENTIALS[0][0]
        password = EMPIRE_MARKET_CREDENTIALS[0][1]
        scrapingSession = EmpireScrapingSession(queue, username, password, nr_of_threads, thread_id=0)
        session_id = scrapingSession.session_id

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
            scrapingSession.populate_queue()
            print("Sleeping 5 seconds to avoid race conditions...")
            sleep(5)

        t = threading.Thread(target=scrapingSession.scrape)
        t.start()

        for i in range(1, self.nr_of_threads):
            username = EMPIRE_MARKET_CREDENTIALS[i][0]
            password = EMPIRE_MARKET_CREDENTIALS[i][1]
            sleep(i * 2)
            scrapingSession = EmpireScrapingSession(queue, username, password, nr_of_threads, thread_id=i,
                                                    session_id=session_id)
            t = threading.Thread(target=scrapingSession.scrape)
            t.start()

        self.first_run = False

    def _should_start_new_session(self) -> bool:
        if self.first_run:
            return True

        if queue_is_empty(self.queue) and self.refill_queue_when_complete:
            return True

        return False

    def _wait_until_midnight_utc(self) -> None:


        utc_current_datetime = datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp())

        utc_next_day_datetime = utc_current_datetime + datetime.timedelta(days=1)

        utc_next_day_date = utc_next_day_datetime.date()

        utc_next_midnight_datetime = datetime.datetime(year=utc_next_day_date.year, month=utc_next_day_date.month,
                                                       day=utc_next_day_date.day)

        while True:
            seconds_until_midnight = (utc_next_midnight_datetime - datetime.datetime.utcnow()).total_seconds()
            if seconds_until_midnight > 0:
                print(f"Waiting until {str(utc_next_midnight_datetime)[:19]} before starting new scraping session.")
                hours = int(seconds_until_midnight//3600)
                minutes = int((seconds_until_midnight - hours * 3600) // 60)
                seconds = int(seconds_until_midnight - hours * 3600 - minutes * 60)
                print(f"{hours} hours, {minutes} minutes and {seconds} seconds left.\n")
                sleep(min(float(30), seconds_until_midnight))
            else:
                return

    def _update_settings(self) -> None:
        settings = get_settings()
        self.refill_queue_when_complete = settings.refill_queue_when_complete
