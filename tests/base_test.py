import pickle
from typing import Any
from unittest import TestCase
from bs4 import BeautifulSoup
from src.utils import get_page_as_soup_html


class BaseTest(TestCase):

    @staticmethod
    def _get_page_as_soup_html(file_name: str, html_dir: str) -> BeautifulSoup:
        with open(html_dir+file_name) as file:
            return get_page_as_soup_html(file.read())

    @staticmethod
    def _get_expected_value(file_name: str, expected_values_dir: str, bytes: bool=True) -> Any:
        if bytes:
            with open(expected_values_dir+file_name,
                      'rb') as f:
                return pickle.load(f)
        else:
            file = open(expected_values_dir+file_name, "r")
            expected_value = file.read()
            file.close()
            return expected_value
