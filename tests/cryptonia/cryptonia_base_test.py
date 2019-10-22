from unittest import TestCase

from definitions import ROOT_DIR
from src.utils import get_page_as_soup_html


class CryptoniaBaseTest(TestCase):

    HTML_DIR = ROOT_DIR+"tests/cryptonia/html_files/"

    @staticmethod
    def _get_page_as_soup_html(file_name):
        return get_page_as_soup_html(CryptoniaBaseTest.HTML_DIR, None, file_name=file_name, use_offline_file=True)
