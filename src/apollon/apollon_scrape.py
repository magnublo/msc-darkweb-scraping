from threading import Lock
from typing import Type

import requests
from requests import Response

from src.base.base_functions import BaseFunctions
from src.base.base_scraper import BaseScraper


class ApollonScrapingSession(BaseScraper):

    def _handle_custom_server_error(self) -> None:
        return

    def _get_market_id(self) -> str:
        return APOLLON_MARKET_ID

    def _get_working_dir(self) -> str:
        pass

    def _get_headers(self) -> dict:
        pass

    def _get_login_url(self) -> str:
        pass

    def _get_is_logged_out_phrase(self) -> str:
        pass

    def populate_queue(self) -> None:
        pass

    def _get_web_session_object(self) -> requests.Session:
        pass

    def _scrape_queue_item(self, *args) -> None:
        pass

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        pass

    def _get_anti_captcha_kwargs(self):
        pass

    def _is_logged_out(self, web_session: requests.Session, response: Response, login_url: str,
                       login_page_phrase: str) -> bool:
        pass

    def _get_successful_login_phrase(self) -> str:
        pass

    def _get_min_credentials_per_thread(self) -> int:
        pass

    def _get_mirror_db_lock(self) -> Lock:
        pass

    def _get_user_credentials_db_lock(self) -> Lock:
        pass

    def _get_mirror_failure_lock(self) -> Lock:
        pass

    def _is_custom_server_error(self, response) -> bool:
        pass