import re
from unittest import TestCase

from src.cryptonia.cryptonia_functions import CryptoniaScrapingFunctions as scrapingFunctions
from tests.cryptonia.cryptonia_base_test import CryptoniaBaseTest

PRODUCT_PAGE_URL_REGEX = r'\/product\/[0-9]{6,8}'
SELLER_URL_REGEX = r"'\/user\/([A-Za-z]|[0-9]|_){2,32}'"


class TestGetCategoryTuplesCategoryUrlsAndNrOfListings(CryptoniaBaseTest):

    def test_get_category_tuples_category_urls_and_nr_of_listings(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_category_index_0")
        category_lists, urls = scrapingFunctions.get_category_lists_and_urls(
            soup_html)
        self.assertEqual(len(category_lists), len(urls))
        self.assertEqual(len(category_lists), 68)
        for category_list in category_lists:
            self.assertEqual(len(category_list), 2)


class TestGetNrOfResultPagesInCategory(CryptoniaBaseTest):

    def test_get_nr_of_result_pages_in_category__zero(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_0")
        nr_of_pages_in_category = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
        self.assertEqual(nr_of_pages_in_category, 111)

    def test_get_nr_of_result_pages_in_category__one(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_1")
        nr_of_pages_in_category = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
        self.assertEqual(nr_of_pages_in_category, 31)


class TestGetProductPageUrls(CryptoniaBaseTest):

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


class TestGetTitlesSellersAndSellerUrls(CryptoniaBaseTest):

    def test_get_titles_sellers_and_seller_urls_zero(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_0")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 25)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_titles_sellers_and_seller_urls_one(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_1")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 25)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_titles_sellers_and_seller_urls_two(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_2")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 2)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_titles_sellers_and_seller_urls_three(self):
        soup_html = self._get_page_as_soup_html(file_name="saved_cryptonia_search_result_in_category_3")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 15)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)


class TestGetCryptocurrencyRates(CryptoniaBaseTest):

    def test_get_cryptocurrency_rates_zero(self):
        soup_html = self._get_page_as_soup_html(file_name=f"saved_cryptonia_search_result_in_category_0")
        btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)
        self.assertEqual(btc_rate, 8210.85)
        self.assertEqual(xmr_rate, 58.369618913071555)

        soup_html = self._get_page_as_soup_html(file_name=f"saved_cryptonia_search_result_in_category_1")
        btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)
        self.assertEqual(btc_rate, 8211.52)
        self.assertEqual(xmr_rate, 58.031961450754984)

        for i in range(2, 4):
            soup_html = self._get_page_as_soup_html(file_name=f"saved_cryptonia_search_result_in_category_{i}")
            btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)
            self.assertEqual(btc_rate, 7382.25)
            self.assertEqual(xmr_rate, 52.643858263761864)
