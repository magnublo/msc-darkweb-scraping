import threading
from time import sleep
from multiprocessing import Queue

from definitions import EMPIRE_MARKET_CREDENTIALS, DEBUG_MODE
from src.empire.scrape import EmpireScrapingSession
from src.utils import get_settings


def queue_is_empty(queue):
    is_empty = queue.empty()
    sleep(300)
    return queue.empty() and is_empty


class EmpireScrapingManager:

    def __init__(self, nr_of_threads=1):
        assert nr_of_threads <= len(EMPIRE_MARKET_CREDENTIALS)
        queue = Queue()
        first_run = True

        settings = get_settings()
        refill_queue_when_complete = settings.refill_queue_when_complete

        while True:
            if first_run or (queue_is_empty(queue) and refill_queue_when_complete):
                username = EMPIRE_MARKET_CREDENTIALS[0][0]
                password = EMPIRE_MARKET_CREDENTIALS[0][1]
                scrapingSession = EmpireScrapingSession(queue, username, password, nr_of_threads, thread_id=0)
                session_id = scrapingSession.session_id

                if DEBUG_MODE:
                    for i in range(0, 1000):
                        queue.put(str(i))
                    sleep(5)
                else:
                    scrapingSession.populate_queue()
                    print("Sleeping 5 seconds to avoid race conditions...")
                    sleep(5)

                t = threading.Thread(target=scrapingSession.scrape)
                t.start()

                for i in range(1, nr_of_threads):
                    username = EMPIRE_MARKET_CREDENTIALS[i][0]
                    password = EMPIRE_MARKET_CREDENTIALS[i][1]
                    sleep(1)
                    scrapingSession = EmpireScrapingSession(queue, username, password, nr_of_threads, thread_id=i, session_id=session_id)
                    t = threading.Thread(target=scrapingSession.scrape)
                    t.start()

                first_run = False
            else:
                sleep(300)
                settings = get_settings()
                refill_queue_when_complete = settings.refill_queue_when_complete
