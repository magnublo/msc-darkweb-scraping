from unittest import TestCase

from definitions import CRYPTONIA_DIR
from src import utils
from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions


class TestCryptoniaScrapingFunctions(TestCase):

    def test_get_category_tuples_category_urls_and_nr_of_listings(self):
        soup_html = utils.get_page_as_soup_html(CRYPTONIA_DIR, None, file_name="saved_cryptonia_category_index_html",
                                                use_offline_file=True)
        list_of_category_list_category_urls_and_nr_of_listings = scrapingFunctions.get_list_of_cateogory_list_and_url(
            soup_html)
        self.assertGreaterEqual(len(list_of_category_list_category_urls_and_nr_of_listings), 1)
