from time import time
from typing import List, Dict

import cfscrape
import requests
from bs4 import BeautifulSoup
from requests import Response
from sqlalchemy import func

from definitions import REFRESH_MIRROR_DB_LIMIT, MINIMUM_WAIT_BETWEEN_MIRROR_DB_REFRESH, DARKFAIL_URL, \
    DARKFAIL_MARKET_STRINGS, MINIMUM_WAIT_TO_RECHECK_DEAD_MIRROR, \
    WEB_EXCEPTIONS_TUPLE, DARKFAIL_MARKET_SUBURLS
from src.base_functions import BaseFunctions
from src.models.listing_observation import ListingObservation
from src.models.market_mirror import MarketMirror
from src.models.scraping_session import ScrapingSession
from src.utils import test_mirror, get_page_as_soup_html, get_schemaed_url, pretty_print_GET, pretty_print_POST, \
    get_response_text


class MirrorManager:

    def __init__(self, scraper):
        self.scraper = scraper
        self.scraper.mirror_base_url = None
        self.web_session = cfscrape.Session()
        self.headers: dict = self._get_headers()

    def get_new_mirror(self) -> str:
        # set failure time for current mirror
        # get mirror with oldest failure time
        # if no mirror with old failure time
        # if db not refreshed last 30 min
        # refresh mirror db
        # recurse
        # test mirror
        # if test failed, recurse

        current_mirror: MarketMirror = self.scraper.db_session.query(MarketMirror).filter(
            MarketMirror.market_id == self.scraper.market_id,
            MarketMirror.url == self.scraper.mirror_base_url).first()

        if current_mirror:
            current_mirror.last_offline_timestamp = time()
            self.scraper.db_session.add(current_mirror)
            self.scraper.db_session.flush()

        # The candidate mirror is the most recently online mirror that has not failed within the last
        # MINIMUM_WAIT_TO_RECHECK_DEAD_MIRROR seconds.
        candidate_mirror: MarketMirror = self.scraper.db_session.query(MarketMirror).filter(
            MarketMirror.last_online_timestamp == self.scraper.db_session.query(
                func.max(MarketMirror.last_online_timestamp)) \
            .filter(MarketMirror.last_offline_timestamp < time() - MINIMUM_WAIT_TO_RECHECK_DEAD_MIRROR) \
            .filter(MarketMirror.market_id == self.scraper.market_id) \
            .subquery().as_scalar()).first()

        if not candidate_mirror and time() - self.scraper.time_last_refreshed_mirror_db > \
                MINIMUM_WAIT_BETWEEN_MIRROR_DB_REFRESH:
            if self.scraper.mirror_db_lock.acquire(False):
                self._refresh_mirror_db()
                self.scraper.mirror_db_lock.release()
                return self.get_new_mirror()
            else:
                self.scraper.logger.warn("Tried refreshing mirror db, but other thread has lock.")
                raise AssertionError("Lock was acquired, but should not be possible in this state.")
        if time() - candidate_mirror.last_offline_timestamp < REFRESH_MIRROR_DB_LIMIT:
            if time() - self.scraper.time_last_refreshed_mirror_db > MINIMUM_WAIT_BETWEEN_MIRROR_DB_REFRESH:
                if self.scraper.mirror_db_lock.acquire(False):
                    self._refresh_mirror_db()
                    self.scraper.mirror_db_lock.release()
                    return self.get_new_mirror()
                else:
                    self.scraper.logger.warn("Tried refreshing mirror db, but other thread has lock.")
            else:
                self.scraper.logger.warn(
                    f"No mirrors have been online last {REFRESH_MIRROR_DB_LIMIT} seconds, but mirror db was refreshed "
                    f"within last {MINIMUM_WAIT_BETWEEN_MIRROR_DB_REFRESH} seconds, so no action taken.")

        mirror_works = test_mirror(candidate_mirror.url, self.scraper.headers, self.scraper.proxy)

        if mirror_works:
            candidate_mirror.last_online_timestamp = time()
            self.scraper.db_session.commit()
            return candidate_mirror.url
        else:
            candidate_mirror.last_offline_timestamp = time()
            self.scraper.db_session.commit()
            return self.get_new_mirror()

    def _refresh_mirror_db(self) -> None:
        self.scraper.logger.info(f"Refreshing mirror db...")
        enter_method_time = time()

        mirror_status_dict: dict = self._get_mirror_status_dict_from_external_overview()  # key: url, val: is_online
        urls_in_retrieved_mirrors: List[str] = [key for key in mirror_status_dict.keys()]

        existing_mirrors: List[MarketMirror] = self.scraper.db_session.query(MarketMirror).filter(
            MarketMirror.market_id == self.scraper.market_id,
            MarketMirror.url.in_(urls_in_retrieved_mirrors)).all()

        existing_mirror: MarketMirror
        for existing_mirror in existing_mirrors:
            existing_mirror_last_online: int = mirror_status_dict[existing_mirror.url]
            existing_mirror.last_online_timestamp = existing_mirror_last_online

        existing_mirror_urls: List[str] = [existing_mirror.url for existing_mirror in existing_mirrors]

        new_mirror_urls = [url for url in urls_in_retrieved_mirrors if url not in existing_mirror_urls]

        nr_of_new_working_mirrors = 0

        for new_mirror_url, new_mirror_last_online in [(url, mirror_status_dict[url]) for url in new_mirror_urls]:
            if new_mirror_last_online > enter_method_time:
                nr_of_new_working_mirrors += 1
                last_offline_timestamp = 0
            else:
                last_offline_timestamp = time()
            last_online_timestamp = new_mirror_last_online
            self.scraper.db_session.add(
                MarketMirror(last_offline_timestamp=last_offline_timestamp, last_online_timestamp=last_online_timestamp,
                             market_id=self.scraper.market_id, url=new_mirror_url))

        self.scraper.db_session.flush()
        self.scraper.time_last_refreshed_mirror_db = time()
        self.scraper.logger.info(
            f"Updated failure timestamps on {len(existing_mirrors)} existing mirrors, and added {len(new_mirror_urls)} "
            f"new mirrors. {nr_of_new_working_mirrors} of these new mirrors appear to be online.")

    def _get_mirror_status_dict_from_external_overview(self) -> dict:
        # get main page
        # get sub page
        # get captcha page
        # get captcha image
        # solve captcha
        # post captcha solution and get redir to all mirrors page
        self.scraper.scraping_funcs: BaseFunctions
        main_page_web_response = self._get_non_market_site_web_response(DARKFAIL_URL)
        main_page_web_response_text = get_response_text(main_page_web_response)
        main_page_soup_html = get_page_as_soup_html(main_page_web_response_text)
        sub_page_url = self.scraper.scraping_funcs.get_sub_url_with_all_market_mirrors(main_page_soup_html,
                                                                                       DARKFAIL_MARKET_STRINGS[
                                                                                           self.scraper.market_id])
        if sub_page_url:
            return self._get_final_page_mirror_status_dict(sub_page_url)
        else:
            return self.scraper.scraping_funcs.get_market_mirrors_from_main_page(main_page_soup_html,
                                                                                 self.scraper.market_id)

    def _get_final_page_mirror_status_dict(self, sub_page_url: str) -> dict:
        self.scraper.scraping_funcs: BaseFunctions
        captcha_page_url = self._get_captcha_page_url(sub_page_url)

        captcha_page_web_response: Response = self._get_non_market_site_web_response(
            f"{DARKFAIL_URL}{captcha_page_url}")

        captcha_page_web_response_text = get_response_text(captcha_page_web_response)
        captcha_page_soup_html: BeautifulSoup = get_page_as_soup_html(captcha_page_web_response_text)

        self._get_stylesheet_cookie(captcha_page_soup_html)

        captcha_base_64_image: str
        id_token: str
        captcha_base_64_image = self.scraper.scraping_funcs.get_captcha_base64_image_from_mirror_overview_page(
            captcha_page_soup_html)

        captcha_solution, solution_response = self.scraper._get_captcha_solution_from_base64_image(
            base64_image=captcha_base_64_image,
            anti_captcha_kwargs={'case': True, 'comment': 'Only type strong colored letters in foreground'})

        captcha_solution_payload: Dict[str, str] = \
            self.scraper.scraping_funcs.get_captcha_solution_payload_to_mirror_overview_page(
                captcha_page_soup_html,
                captcha_solution)

        captcha_solution_post_url: str = self.scraper.scraping_funcs.get_captcha_solution_post_url(
            captcha_page_soup_html)

        captcha_post_req_referer_header = f"{get_schemaed_url(DARKFAIL_URL, 'https')}/" \
                                          f"captcha/{DARKFAIL_MARKET_SUBURLS[self.scraper.market_id]}"

        final_page_web_response: Response = self._get_non_market_site_web_response(
            f"{DARKFAIL_URL}{captcha_solution_post_url}", post_data=captcha_solution_payload,
            referer={"referer": captcha_post_req_referer_header})

        final_page_web_response_text = get_response_text(final_page_web_response)
        final_page_soup_html: BeautifulSoup = get_page_as_soup_html(final_page_web_response_text)

        if self.scraper.scraping_funcs.captcha_solution_was_wrong(final_page_soup_html):
            self.scraper.logger.warn("Wrong captcha solution. Retrying.")
            self.scraper.anti_captcha_control.complaint_on_result(int(solution_response["taskId"]), "image")
            self.scraper._add_captcha_solution(captcha_base_64_image, captcha_solution, correct=False, website="DARKFAIL")
            return self._get_final_page_mirror_status_dict(sub_page_url)
        else:
            self.scraper._add_captcha_solution(captcha_base_64_image, captcha_solution, correct=True, website="DARKFAIL")
            return self.scraper.scraping_funcs.get_market_mirrors_from_final_page(final_page_soup_html)

    def _get_captcha_page_url(self, sub_page_url: str) -> str:
        self.scraper.scraping_funcs: BaseFunctions
        sub_page_web_response: Response = self._get_non_market_site_web_response(
            f"{DARKFAIL_URL}{sub_page_url}")
        sub_page_web_response_text = get_response_text(sub_page_web_response)
        sub_page_soup_html: BeautifulSoup = get_page_as_soup_html(sub_page_web_response_text)
        return self.scraper.scraping_funcs.get_captcha_page_url(sub_page_soup_html)

    def _has_scraped_at_least_one_item(self) -> bool:
        existing_listing_observation_id: int = self.scraper.db_session.query(ListingObservation).with_entities(
            ListingObservation.id).filter(
            ListingObservation.session_id == self.scraper.db_session.query(
                func.max(ScrapingSession.id)) \
            .filter(ListingObservation.thread_id == self.scraper.thread_id)
            .subquery().as_scalar()).first()

        return existing_listing_observation_id == True

    def _get_non_market_site_web_response(self, unschemaed_url: str, post_data: dict = None,
                                          scehma: str = "https", referer: dict = None) -> Response:
        headers = self.headers
        if referer is not None:
            headers.update(referer)
        url = get_schemaed_url(unschemaed_url, schema=scehma)
        http_verb = 'POST' if post_data else 'GET'
        kwargs = {"method": http_verb, 'url': url, 'data': post_data, 'headers': headers}
        max_tries = 10
        if http_verb == 'GET': self.scraper.logger.debug(
            pretty_print_GET(self.web_session.prepare_request(requests.Request(**kwargs))))
        if http_verb == 'POST': self.scraper.logger.debug(pretty_print_POST(
            self.web_session.prepare_request(
                requests.Request(**kwargs))))
        for _ in range(max_tries):
            try:
                response = self.web_session.request(**kwargs)
                if unschemaed_url.find(DARKFAIL_URL) != -1:
                    response_text = get_response_text(response)
                    soup_html = get_page_as_soup_html(response_text)
                    self._get_stylesheet_cookie(soup_html)
                return response
            except WEB_EXCEPTIONS_TUPLE as e:
                self.scraper.logger.warning(type(e))

    def _get_stylesheet_cookie(self, captcha_page_soup_html):
        self.scraper.scraping_funcs: BaseFunctions
        style_sheet_url = self.scraper.scraping_funcs.get_stylesheet_url_from_arbitrary_mirror_overview_site_page(
            captcha_page_soup_html)
        if style_sheet_url:
            self._get_non_market_site_web_response(f"{DARKFAIL_URL}{style_sheet_url}", post_data=None, scehma="https",
                                                   referer=None)

    def _get_headers(self) -> dict:
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,nb;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            # referer: https://dark.fail/captcha/cryptonia
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 "
                          "Safari/537.36"
        }
