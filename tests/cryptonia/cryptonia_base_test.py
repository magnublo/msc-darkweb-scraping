import pickle
from typing import Any
from unittest import TestCase

from bs4 import BeautifulSoup

from definitions import ROOT_DIR
from src.utils import get_page_as_soup_html


class CryptoniaBaseTest(TestCase):

    TESTS_DIR = ROOT_DIR + "tests/cryptonia/"
    HTML_DIR = TESTS_DIR + "html_files/"
    EXPECTED_VALUES_DIR = TESTS_DIR + "expected_values/"

    @staticmethod
    def _get_page_as_soup_html(file_name: str) -> BeautifulSoup:
        with open(CryptoniaBaseTest.HTML_DIR+file_name) as file:
            return get_page_as_soup_html(file.read())

    @staticmethod
    def _get_expected_value(file_name: str, bytes: bool=True) -> Any:
        if bytes:
            with open(CryptoniaBaseTest.EXPECTED_VALUES_DIR+file_name,
                      'rb') as f:
                return pickle.load(f)
        else:
            file = open(CryptoniaBaseTest.EXPECTED_VALUES_DIR+file_name, "r")
            expected_value = file.read()
            file.close()
            return expected_value
