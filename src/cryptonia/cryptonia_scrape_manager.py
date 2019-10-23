from typing import List

from definitions import CRYPTONIA_MARKET_CREDENTIALS, CRYPTONIA_MARKET_ID
from src.base_scraper import BaseScraper
from src.base_scraping_manager import BaseScrapingManager
from src.cryptonia.cryptonia_scrape import CryptoniaMarketScraper
from src.models.settings import Settings


class CryptoniaScrapingManager(BaseScrapingManager):

    def _get_market_credentials(self) -> List[List[str]]:
        return CRYPTONIA_MARKET_CREDENTIALS

    def _get_scraping_session(self, queue, username, password, nr_of_threads, thread_id,
                              session_id=None) -> BaseScraper:
        return CryptoniaMarketScraper(queue, username, password, nr_of_threads, thread_id, session_id=session_id)

    def _get_market_name(self) -> str:
        return CRYPTONIA_MARKET_ID

    def __init__(self, settings: Settings, nr_of_threads: int):
        super().__init__(settings, nr_of_threads)
