from unittest import TestCase, skip
from unittest.mock import patch, Mock

import src.main
from definitions import ROOT_DIR
from tests.integration.mocks.mocked_dynamic_config import mocked_get_logger_config, MOCKED_WEBSITES_TO_BE_SCRAPED
from tests.integration.mocks.mocked_scraping_manager import MockedScrapingManager

TESTS_DIR = ROOT_DIR + "tests/empire/"
HTML_DIR = TESTS_DIR + "html_files/"


def mocked_get_user_input():
    return (4, None, True), (0, None, True)


class TestMain(TestCase):

    @patch('src.main.get_user_input', side_effect=mocked_get_user_input)
    @patch('src.main.WEBSITES_TO_BE_SCRAPED', MOCKED_WEBSITES_TO_BE_SCRAPED)
    @patch('src.main.get_logger_config', side_effect=mocked_get_logger_config)
    @skip("Integration test with many dependencies")
    def test_main(self, mocked_get_user_input: Mock, mocked_get_logger_config):
        with patch('src.main.ScrapingManager', MockedScrapingManager):
            src.main.run()
