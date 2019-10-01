import threading
from multiprocessing import Queue
from time import sleep

from definitions import EMPIRE_MARKET_CREDENTIALS
from src.base import Session
from src.empire.scrape import EmpireScrapingSession


class EmpireScrapingManager:

    def __init__(self, nr_of_threads=1):
        assert nr_of_threads <= len(EMPIRE_MARKET_CREDENTIALS)

        queue = Queue()

        username = EMPIRE_MARKET_CREDENTIALS[0][0]
        password = EMPIRE_MARKET_CREDENTIALS[0][1]

        db_sesssion = Session()
        scrapingSession = EmpireScrapingSession(queue, username, password, db_sesssion, thread_id=0)
        session_id = scrapingSession.session_id
        scrapingSession.populate_queue()

        print("Sleeping 5 seconds to avoid race conditions...")
        sleep(5)

        t = threading.Thread(target=scrapingSession.scrape)
        t.start()

        for i in range(1, nr_of_threads):
            username = EMPIRE_MARKET_CREDENTIALS[i][0]
            password = EMPIRE_MARKET_CREDENTIALS[i][1]
            db_sesssion = Session()
            scrapingSession = EmpireScrapingSession(queue, username, password, db_sesssion, thread_id=i, session_id=session_id)
            t = threading.Thread(target=scrapingSession.scrape)
            t.start()