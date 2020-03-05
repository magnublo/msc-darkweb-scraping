from threading import Lock
from typing import Type

import requests
from requests import Response

from definitions import DREAM_MARKET_ID, DREAM_SRC_DIR
from src.base.base_functions import BaseFunctions
from src.base.base_scraper import BaseScraper
from src.utils import PageType


class DreamScrapingSession(BaseScraper):

    def __init__(self, queue: Queue, nr_of_threads: int, thread_id: int,
                 proxy: dict, session_id: int):


    def _handle_custom_server_error(self) -> None:
        return

    def _get_market_id(self) -> str:
        return DREAM_MARKET_ID

    def _get_working_dir(self) -> str:
        return DREAM_SRC_DIR

    def _get_headers(self) -> dict:
        return {}

    def _get_login_url(self) -> str:
        return ""

    def _get_is_logged_out_phrase(self) -> str:
        return "sdwaed"

    def populate_queue(self) -> None:
        self.queue

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

    def _apply_processing_to_captcha_image(self, image_response, captcha_instruction):
        pass

    def _captcha_instruction_is_generic(self, captcha_instruction: str) -> bool:
        pass

    def _is_expected_page(self, response: requests.Response, expected_page_type: PageType) -> bool:
        pass

    def _get_captcha_image_request_headers(self, headers: dict) -> dict:
        pass