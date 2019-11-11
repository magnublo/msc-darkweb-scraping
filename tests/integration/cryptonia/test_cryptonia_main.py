from unittest import TestCase, skip
from unittest.mock import patch, Mock

import src.main
from definitions import ROOT_DIR
from tests.integration.mocks.mocked_dynamic_config import MOCKED_WEBSITES_TO_BE_SCRAPED_CRYPTONIA, \
    mocked_get_logger_config
from tests.integration.mocks.mocked_scraping_manager import MockedScrapingManager

TESTS_DIR = ROOT_DIR + "tests/cryptonia/"
HTML_DIR = TESTS_DIR + "html_files/"


class TestMain(TestCase):

    @patch('src.main.WEBSITES_TO_BE_SCRAPED', MOCKED_WEBSITES_TO_BE_SCRAPED_CRYPTONIA)
    @patch('src.main.get_logger_config', side_effect=mocked_get_logger_config)
    #@skip("Integration test with many dependencies")
    def test_cryptonia_main(self, mocked_get_logger_config):
        with patch('src.main.ScrapingManager', MockedScrapingManager):
            src.main.run()
