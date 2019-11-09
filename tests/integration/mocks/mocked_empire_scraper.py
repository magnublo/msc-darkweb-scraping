from multiprocessing import Queue

from src.empire.empire_scrape import EmpireScrapingSession


class MockedEmpireScrapingSession(EmpireScrapingSession):

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int, proxy: dict,
             session_id: int):
        super().__init__(queue, nr_of_threads, thread_id, proxy, session_id)