from typing import Any

from bs4 import BeautifulSoup

from definitions import ROOT_DIR
from tests.base_test import BaseTest

TESTS_DIR = ROOT_DIR + "tests/cryptonia/"
HTML_DIR = TESTS_DIR + "html_files/"
EXPECTED_VALUES_DIR = TESTS_DIR + "expected_values/"


class CryptoniaBaseTest(BaseTest):

    @staticmethod
    def _get_page_as_soup_html(file_name: str, html_dir: str = HTML_DIR) -> BeautifulSoup:
        return BaseTest._get_page_as_soup_html(file_name=file_name, html_dir=html_dir)

    @staticmethod
    def _get_expected_value(file_name: str, expected_values_dir: str = EXPECTED_VALUES_DIR, bytes: bool=True) -> Any:
        return BaseTest._get_expected_value(file_name=file_name, expected_values_dir=expected_values_dir, bytes=bytes)
