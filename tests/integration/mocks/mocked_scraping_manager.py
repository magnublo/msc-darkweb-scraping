from src.base.base_scraper import BaseScraper
from src.base.base_scraping_manager import ScrapingManager


class MockedScrapingManager(ScrapingManager):

    def _populate_queue_and_sleep(self, scraping_session: BaseScraper):
        scraping_session.populate_queue()