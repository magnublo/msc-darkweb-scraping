import threading
from multiprocessing import Queue
from time import sleep

from definitions import EMPIRE_MARKET_CREDENTIALS, DEBUG_MODE
from src.base import Session, engine, Base
from src.empire.scrape import EmpireScrapingSession


def queue_is_empty(queue):
    is_empty = queue.empty()
    sleep(300)
    return queue.empty() and is_empty


class EmpireScrapingManager:

    def __init__(self, nr_of_threads=1):
        assert nr_of_threads <= len(EMPIRE_MARKET_CREDENTIALS)
        Base.metadata.create_all(engine)
        queue = Queue()
        first_run = True

        while True:
            if first_run or queue_is_empty(queue):
                username = EMPIRE_MARKET_CREDENTIALS[0][0]
                password = EMPIRE_MARKET_CREDENTIALS[0][1]

                db_sesssion = Session()
                scrapingSession = EmpireScrapingSession(queue, username, password, db_sesssion, nr_of_threads, thread_id=0)
                session_id = scrapingSession.session_id

                if DEBUG_MODE:
                    for i in range(0, 100):
                        queue.put(str(i))
                else:
                    scrapingSession.populate_queue()
                    print("Sleeping 5 seconds to avoid race conditions...")
                    sleep(5)

                t = threading.Thread(target=scrapingSession.scrape)
                t.start()

                for i in range(1, nr_of_threads):
                    username = EMPIRE_MARKET_CREDENTIALS[i][0]
                    password = EMPIRE_MARKET_CREDENTIALS[i][1]
                    db_sesssion = Session()
                    scrapingSession = EmpireScrapingSession(queue, username, password, db_sesssion, nr_of_threads, thread_id=i, session_id=session_id)
                    t = threading.Thread(target=scrapingSession.scrape)
                    t.start()

                first_run = False

            else:
                sleep(300)