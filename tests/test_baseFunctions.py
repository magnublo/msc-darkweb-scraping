from datetime import datetime
from typing import List
from unittest import TestCase

from definitions import ROOT_DIR, DARKFAIL_MARKET_STRINGS
from src.base.base_functions import BaseFunctions as scrapingFunctions
from tests.base_test import BaseTest

TESTS_DIR = ROOT_DIR + "tests/"
HTML_DIR = TESTS_DIR + "html_files/"
EXPECTED_VALUES_DIR = TESTS_DIR + "expected_values/"


class TestGetSubUrlWithAllMarketMirrors(BaseTest):
    def test_get_sub_url_with_all_market_mirrors(self):
        sub_urls: List[str] = []

        for market_string in [val for val in [v for v in DARKFAIL_MARKET_STRINGS.values()][:3]] + ['dark.fail']:
            soup_html = self._get_page_as_soup_html("saved_darkfail_main_page", html_dir=HTML_DIR)
            sub_url_with_all_market_mirrors = scrapingFunctions.get_sub_url_with_all_market_mirrors(soup_html,
                                                                                                    market_string)
            sub_urls.append(sub_url_with_all_market_mirrors)

        self.assertListEqual(['/empire', '/cryptonia', '/samsara', None], sub_urls)


class TestGetMarketMirrorsFromFinalPage(BaseTest):

    def test_get_market_mirrors_from_final_page(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_final_page", html_dir=HTML_DIR)
        market_mirrors = scrapingFunctions.get_market_mirrors_from_final_page(soup_html)
        self.assertEqual(datetime.fromisoformat("2019-11-02 17:48:45"),
                         datetime.utcfromtimestamp(market_mirrors['apai6fp3b6n3n3pa.onion']))


class TestGetMarketMirrorsFromMainPage(BaseTest):
    def test_get_market_mirrors_from_main_page(self):
        all_market_mirrors = {}
        for market_string in [s for s in [k for k in DARKFAIL_MARKET_STRINGS.values()][:3]]:
            soup_html = self._get_page_as_soup_html("saved_darkfail_main_page", html_dir=HTML_DIR)
            market_mirrors = scrapingFunctions.get_market_mirrors_from_main_page(soup_html, market_string)
            all_market_mirrors.update(market_mirrors)

        online_count = 0
        offline_count = 0

        for key in all_market_mirrors.keys():
            if all_market_mirrors[key] == 0:
                offline_count += 1
            else:
                online_count += 1
        self.assertEqual(5, offline_count)
        self.assertEqual(6, online_count)


class TestGetCaptchaPageUrl(BaseTest):
    def test_get_captcha_page_url(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_sub_page", html_dir=HTML_DIR)
        captcha_page_url = scrapingFunctions.get_captcha_page_url(soup_html)
        self.assertEqual("/captcha/empire", captcha_page_url)


class TestGetCaptchaBase64ImageIdTokenAndSolutionPostUrlFromMirrorOverviewPage(BaseTest):
    def test_get_captcha_base64_image_id_token_and_solution_post_url_from_mirror_overview_page_zero(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_0", html_dir=HTML_DIR)
        base64_image = scrapingFunctions.get_captcha_base64_image_from_mirror_overview_page(soup_html)
        expected_value = self._get_expected_value("saved_darkfail_base64_captcha_image_0",
                                                  expected_values_dir=EXPECTED_VALUES_DIR, bytes=False)
        self.assertEqual(expected_value, base64_image)

    def test_get_captcha_base64_image_id_token_and_solution_post_url_from_mirror_overview_page_two(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_2", html_dir=HTML_DIR)
        base64_image = scrapingFunctions.get_captcha_base64_image_from_mirror_overview_page(soup_html)
        expected_value = self._get_expected_value("saved_darkfail_base64_captcha_image_1",
                                                  expected_values_dir=EXPECTED_VALUES_DIR, bytes=False)
        self.assertEqual(expected_value, base64_image)


class TestGetCaptchaSolutionPayloadToMirrorOverviewPage(BaseTest):
    def test_get_captcha_solution_payload_to_mirror_overview_page_zero(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_0", html_dir=HTML_DIR)
        solution_payload = scrapingFunctions.get_captcha_solution_payload_to_mirror_overview_page(soup_html,
                                                                                                  "some_solution",
                                                                                                  "captcha", 'id')
        self.assertEqual({'id': '1hT7fR0Su2BGsk4Sj1m8', 'captcha': 'some_solution'}, solution_payload)

    def test_get_captcha_solution_payload_to_mirror_overview_page_three(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_3", html_dir=HTML_DIR)
        solution_payload = scrapingFunctions.get_captcha_solution_payload_to_mirror_overview_page(soup_html,
                                                                                                  "some_solution",
                                                                                                  "captcha", 'peace')
        self.assertEqual({'peace': '9BVfAyOV7t6utkz1GyQm', 'captcha': 'some_solution'}, solution_payload)


class TestCaptchaSolutionWasWrong(BaseTest):

    def test_captcha_solution_was_wrong_zero(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_0", html_dir=HTML_DIR)
        solution_was_wrong = scrapingFunctions.captcha_solution_was_wrong(soup_html)
        self.assertEqual(False, solution_was_wrong)

    def test_captcha_solution_was_wrong_one(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_1", html_dir=HTML_DIR)
        solution_was_wrong = scrapingFunctions.captcha_solution_was_wrong(soup_html)
        self.assertEqual(True, solution_was_wrong)


class TestGetStylesheetUrlFromMirrorSiteCaptchaPage(BaseTest):

    def test_get_stylesheet_url_from_mirror_site_captcha_page(self):
        for i in range(2):
            soup_html = self._get_page_as_soup_html(f"saved_darkfail_captcha_page_{i}", html_dir=HTML_DIR)
            css_link = scrapingFunctions.get_stylesheet_url_from_arbitrary_mirror_overview_site_page(soup_html)
            self.assertEqual("/css/style.css", css_link)


class TestGetCaptchaPostParameterName(BaseTest):
    def test_get_captcha_post_parameter_name_two(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_2", html_dir=HTML_DIR)
        captcha_post_parameter_name = scrapingFunctions.get_captcha_post_parameter_name(soup_html)
        self.assertEqual("zooko", captcha_post_parameter_name)

    def test_get_captcha_post_parameter_name_three(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_3", html_dir=HTML_DIR)
        captcha_post_parameter_name = scrapingFunctions.get_captcha_post_parameter_name(soup_html)
        self.assertEqual("love", captcha_post_parameter_name)

    def test_get_captcha_post_parameter_name_four(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_4", html_dir=HTML_DIR)
        captcha_post_parameter_name = scrapingFunctions.get_captcha_post_parameter_name(soup_html)
        self.assertEqual("tock", captcha_post_parameter_name)

class TestGetCaptchaIdParameterName(BaseTest):

    def test_get_captcha_id_parameter_name_zero(self):
        soup_html = self._get_page_as_soup_html("saved_darkfail_captcha_page_3", html_dir=HTML_DIR)
        id_parameter_name = scrapingFunctions.get_captcha_id_parameter_name(soup_html)
        self.assertEqual("peace", id_parameter_name)
