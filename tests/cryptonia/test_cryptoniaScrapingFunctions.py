import re

from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions
from tests.cryptonia.cryptonia_base_test import CryptoniaBaseTest

PRODUCT_PAGE_URL_REGEX = r'\/product\/[0-9]{8}'

class TestCryptoniaScrapingFunctions(CryptoniaBaseTest):

    def test_get_category_tuples_category_urls_and_nr_of_listings(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_category_index_0")
        category_lists, urls = scrapingFunctions.get_category_lists_and_urls(
            soup_html)
        self.assertEqual(len(category_lists), len(urls))
        self.assertEqual(len(category_lists), 68)
        for category_list in category_lists:
            self.assertEqual(len(category_list), 2)

    def test_get_nr_of_result_pages_in_category__zero(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_0")
        nr_of_pages_in_category = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
        self.assertEqual(nr_of_pages_in_category, 111)

    def test_get_nr_of_result_pages_in_category__one(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_1")
        nr_of_pages_in_category = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
        self.assertEqual(nr_of_pages_in_category, 31)

    def test_get_product_page_urls_zero(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_0")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 25)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_product_page_urls_one(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_1")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 25)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_product_page_urls_two(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_2")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 2)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_product_page_urls_three(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_3")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 15)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)
