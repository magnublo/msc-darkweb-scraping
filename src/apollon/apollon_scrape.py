from random import shuffle
from threading import Lock
from typing import Type, Tuple, List

import requests
from bs4 import BeautifulSoup
from requests import Response

from definitions import APOLLON_MARKET_ID, APOLLON_MARKET_GENERIC_CAPTCHA_INSTRUCTIONS, APOLLON_SRC_DIR, \
    APOLLON_HTTP_HEADERS, APOLLON_MIN_CREDENTIALS_PER_THREAD, APOLLON_MARKET_CATEGORY_INDEX_URL_PATH, \
    APOLLON_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE
from src.apollon.apollon_functions import ApollonScrapingFunctions
from src.base.base_functions import BaseFunctions
from src.base.base_scraper import BaseScraper
from src.db_utils import get_column_name
from src.models.scraping_session import ScrapingSession
from src.utils import PageType, get_page_as_soup_html


class ApollonScrapingSession(BaseScraper):


    __mirror_manager_lock__ = Lock()
    __user_credentials_db_lock__ = Lock()
    __mirror_failure_lock__ = Lock()

    def _apply_processing_to_captcha_image(self, image_response, captcha_instruction):
        raise NotImplementedError('')

    def _captcha_instruction_is_generic(self, captcha_instruction: str) -> bool:
        return captcha_instruction in APOLLON_MARKET_GENERIC_CAPTCHA_INSTRUCTIONS

    def _is_expected_page(self, response: requests.Response, expected_page_type: PageType) -> bool:
        return True
        # LISTING = "listing",
        # SELLER = "seller",
        # FEEDBACK = "feedback",
        # PGP = "PGP key",
        # SEARCH_RESULT = "search result",
        # UNDEFINED = "arbitrary"

        # soup_html = get_page_as_soup_html(response.text)
        #
        # self.scraping_funcs: EmpireScrapingFunctions
        #
        # if expected_page_type == expected_page_type.LISTING:
        #     return self.scraping_funcs.is_listing(soup_html)
        # elif expected_page_type == expected_page_type.SELLER:
        #     return self.scraping_funcs.is_seller(soup_html)
        # elif expected_page_type == expected_page_type.FEEDBACK:
        #     return self.scraping_funcs.is_feedback(soup_html)
        # elif expected_page_type == expected_page_type.PGP:
        #     return self.scraping_funcs.is_pgp_key(soup_html)
        # elif expected_page_type == expected_page_type.SEARCH_RESULT:
        #     return self.scraping_funcs.is_search_result(soup_html)
        # elif expected_page_type == expected_page_type.CATEGORY_INDEX:
        #     return self.scraping_funcs.is_category_index(soup_html)
        # elif expected_page_type == expected_page_type.UNDEFINED:
        #     return True

    def _handle_custom_server_error(self) -> None:
        raise NotImplementedError('')

    def _get_captcha_image_request_headers(self, headers: dict) -> dict:
        new_headers = headers
        new_headers["Accept"] = "image/webp,image/apng,image/*,*/*;q=0.8"
        new_headers["Referer"] = f"{self.mirror_base_url}{self._get_login_url()}"
        return new_headers

    def _get_market_id(self) -> str:
        return APOLLON_MARKET_ID

    def _get_working_dir(self) -> str:
        return APOLLON_SRC_DIR

    def _get_headers(self) -> dict:
        return APOLLON_HTTP_HEADERS

    def _get_login_url(self) -> str:
        return "/login.php"

    def _get_is_logged_out_phrase(self) -> str:
        return ""

    def _get_scraping_funcs(self) -> Type[BaseFunctions]:
        return ApollonScrapingFunctions

    def _get_anti_captcha_kwargs(self):
        return {
            'numeric': 0,
            'case': True,
            'comment': "ignore URL in bottom of image"
        }

    def _is_logged_out(self, web_session: requests.Session, response: Response, login_url: str,
                       login_page_phrase: str) -> bool:
        soup_html = get_page_as_soup_html(response.text)
        return not self.scraping_funcs.is_logged_in(soup_html, self.web_session.username)

    def _get_min_credentials_per_thread(self) -> int:
        return APOLLON_MIN_CREDENTIALS_PER_THREAD

    def _get_mirror_db_lock(self) -> Lock:
        return self.__mirror_manager_lock__

    def _get_user_credentials_db_lock(self) -> Lock:
        return self.__user_credentials_db_lock__

    def _get_mirror_failure_lock(self) -> Lock:
        return self.__mirror_failure_lock__

    def _is_custom_server_error(self, response) -> bool:
        return False

    def _get_web_session_object(self) -> requests.Session:
        return requests.session()

    def populate_queue(self) -> None:
        task_list: List[Tuple[any, str]] = []

        self.logger.info(f"Fetching {APOLLON_MARKET_CATEGORY_INDEX_URL_PATH} and creating task queue...")
        web_response = self._get_logged_in_web_response(APOLLON_MARKET_CATEGORY_INDEX_URL_PATH,
                                                        expected_page_type=PageType.CATEGORY_INDEX)
        soup_html = get_page_as_soup_html(web_response.text)

        self.scraping_funcs: ApollonScrapingFunctions

        main_category_index_urls, parent_sub_category_index_urls = \
            self.scraping_funcs.get_sub_categories_index_urls(
                soup_html)

        for parent_sub_category_index_url in parent_sub_category_index_urls:
            self.logger.info(f"Fetching {self.mirror_base_url}{parent_sub_category_index_url}...")
            web_response = self._get_logged_in_web_response(parent_sub_category_index_url)
            soup_html = get_page_as_soup_html(web_response.text)
            tasks = self.scraping_funcs.get_task_list_from_parent_sub_category_page(soup_html)
            for t in tasks:
                task_list.append(t)

        for main_category_index_url in main_category_index_urls:
            self.logger.info(f"Fetching {self.mirror_base_url}{main_category_index_url}...")
            web_response = self._get_logged_in_web_response(main_category_index_url)
            soup_html = get_page_as_soup_html(web_response.text)
            tasks = self.scraping_funcs.get_task_list_from_main_category_page(soup_html)
            for t in tasks:
                task_list.append(t)

        shuffle(task_list)

        for task in task_list:
            self.queue.put(task)

        self.logger.info(f"Queue has been populated with {len(task_list)} tasks.")
        self.initial_queue_size = self.queue.qsize()
        self.db_session.query(ScrapingSession).filter(ScrapingSession.id == self.session_id).update(
            {get_column_name(ScrapingSession.initial_queue_size): self.initial_queue_size})
        self.db_session.commit()

    def _scrape_queue_item(self, category_pair: Tuple[Tuple[str, int, str, int]],
                           search_result_url: str) -> None:
        self.scraping_funcs: ApollonScrapingFunctions

        web_response = self._get_logged_in_web_response(search_result_url, expected_page_type=PageType.SEARCH_RESULT)

        soup_html: BeautifulSoup = get_page_as_soup_html(web_response.text)
        product_page_urls, urls_is_sticky, titles, sellers, seller_urls, nrs_of_views = \
            self.scraping_funcs.get_listing_infos(
                soup_html)

        if len(product_page_urls) == 0:
            if soup_html.text.find(APOLLON_MARKET_INVALID_SEARCH_RESULT_URL_PHRASE) == -1:
                raise AssertionError  # raise error if no logical reason why search result is empty
            else:
                return

        btc_rate, xmr_rate, bch_rate, ltc_rate = self.scraping_funcs.get_cryptocurrency_rates(soup_html)

        assert len(titles) == len(sellers) == len(seller_urls) == len(product_page_urls) == len(urls_is_sticky) == len(
            nrs_of_views)

        for title, seller_name, seller_url, product_page_url, is_sticky, nr_of_views in zip(titles, sellers,
                                                                                            seller_urls,
                                                                                            product_page_urls,
                                                                                            urls_is_sticky,
                                                                                            nrs_of_views):
            self._db_error_catch_wrapper(self.db_session, title, seller_name, seller_url, product_page_url,
                                         is_sticky, nr_of_views, btc_rate, ltc_rate, xmr_rate,
                                         func=self._scrape_listing)
