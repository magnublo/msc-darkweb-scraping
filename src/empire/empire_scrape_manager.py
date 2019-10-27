from typing import List

from definitions import EMPIRE_MARKET_CREDENTIALS, EMPIRE_MARKET_ID
from src.base_scraper import BaseScraper
from src.base_scraping_manager import BaseScrapingManager
from src.empire.empire_scrape import EmpireScrapingSession
from src.models.settings import Settings


class EmpireScrapingManager(BaseScrapingManager):

    def _get_market_credentials(self) -> List[List[str]]:
        return EMPIRE_MARKET_CREDENTIALS

    def _get_scraping_session(self, queue, username, password, nr_of_threads, thread_id,
                              session_id=None) -> BaseScraper:
        return EmpireScrapingSession(queue, username, password, nr_of_threads, thread_id, session_id=session_id)

    def _get_market_name(self) -> str:
        return EMPIRE_MARKET_ID

    def __init__(self, settings: Settings, nr_of_threads: int, initial_session_id: int, proxies: List[dict]):
        super().__init__(settings, nr_of_threads, initial_session_id, proxies)


