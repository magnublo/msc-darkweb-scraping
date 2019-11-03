import re
from datetime import datetime

import demoji

from definitions import MYSQL_TEXT_COLUMN_MAX_LENGTH
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
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_0")
        nr_of_pages_in_category = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
        self.assertEqual(nr_of_pages_in_category, 111)

    def test_get_nr_of_result_pages_in_category__one(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_1")
        nr_of_pages_in_category = scrapingFunctions.get_nr_of_result_pages_in_category(soup_html)
        self.assertEqual(nr_of_pages_in_category, 31)


class TestGetProductPageUrls(CryptoniaBaseTest):

    def test_get_product_page_urls_zero(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_0")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 25)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_product_page_urls_one(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_1")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 25)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_product_page_urls_two(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_2")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 2)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_product_page_urls_three(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_3")
        product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
        self.assertEqual(len(product_page_urls), 15)

        for url in product_page_urls:
            rs = re.findall(PRODUCT_PAGE_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)


class TestGetTitlesSellersAndSellerUrls(CryptoniaBaseTest):

    def test_get_titles_sellers_and_seller_urls_zero(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_0")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 25)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_titles_sellers_and_seller_urls_one(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_1")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 25)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_titles_sellers_and_seller_urls_two(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_2")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 2)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)

    def test_get_titles_sellers_and_seller_urls_three(self):
        soup_html = self._get_page_as_soup_html(file_name="search_results/saved_cryptonia_search_result_in_category_3")
        titles, sellers, seller_urls = scrapingFunctions.get_titles_sellers_and_seller_urls(soup_html)
        self.assertEqual(len(titles), 15)

        for url in seller_urls:
            rs = re.findall(SELLER_URL_REGEX, url)
            self.assertNotEqual(len(rs), -1)


class TestGetCryptocurrencyRates(CryptoniaBaseTest):

    def test_get_cryptocurrency_rates_zero(self):
        soup_html = self._get_page_as_soup_html(file_name=f"search_results/saved_cryptonia_search_result_in_category_0")
        btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)
        self.assertEqual(9237.02, btc_rate)
        self.assertEqual(62.17281132483579, xmr_rate)

        soup_html = self._get_page_as_soup_html(file_name=f"search_results/saved_cryptonia_search_result_in_category_1")
        btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)
        self.assertEqual(btc_rate, 8211.52)
        self.assertEqual(xmr_rate, 58.031961450754984)

        for i in range(2, 4):
            soup_html = self._get_page_as_soup_html(
                file_name=f"search_results/saved_cryptonia_search_result_in_category_{i}")
            btc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)
            self.assertEqual(btc_rate, 7382.25)
            self.assertEqual(xmr_rate, 52.643858263761864)


class TestGetDescription(CryptoniaBaseTest):

    def test_get_description_zero(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_0")
        description = scrapingFunctions.get_description(soup_html)
        description_length = len(description)
        self.assertLessEqual(description_length, MYSQL_TEXT_COLUMN_MAX_LENGTH)
        description = demoji.replace(description)
        self.assertEqual(len(description), description_length)

    def test_get_description_nine(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_9")
        description = scrapingFunctions.get_description(soup_html)
        description_length = len(description)
        self.assertLessEqual(description_length, MYSQL_TEXT_COLUMN_MAX_LENGTH)
        description = demoji.replace(description)
        self.assertEqual(len(description), description_length)


class TestAcceptsCurrencies(CryptoniaBaseTest):

    def test_accepts_currencies_zero(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_0")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_btc, accepts_btc_multisig)
        self.assertEqual(accepts_btc_multisig, accepts_xmr)
        self.assertEqual(accepts_xmr, True)

    def test_accepts_currencies_one(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_1")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_btc, accepts_xmr)
        self.assertEqual(accepts_xmr, True)
        self.assertEqual(accepts_btc_multisig, False)

    def test_accepts_currencies_two(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_2")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_xmr, accepts_btc_multisig)
        self.assertEqual(accepts_xmr, False)

        self.assertEqual(accepts_btc, True)

    def test_accepts_currencies_three(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_3")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_xmr, accepts_btc)
        self.assertEqual(accepts_xmr, True)

    def test_accepts_currencies_four(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_4")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_xmr, accepts_btc)
        self.assertEqual(accepts_btc, True)

        self.assertEqual(accepts_btc_multisig, False)

    def test_accepts_currencies_five(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_5")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_xmr, accepts_btc_multisig)
        self.assertEqual(accepts_btc_multisig, accepts_btc)

        self.assertEqual(accepts_btc, True)

    def test_accepts_currencies_six(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_6")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_xmr, accepts_btc_multisig)
        self.assertEqual(accepts_btc_multisig, accepts_btc)

        self.assertEqual(accepts_btc, True)

    def test_accepts_currencies_seven(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_7")
        accepts_btc, accepts_btc_multisig, accepts_xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual(accepts_xmr, accepts_btc)
        self.assertEqual(accepts_btc, True)

        self.assertEqual(accepts_btc_multisig, False)


class TestGetFiatCurrencyAndPriceAndUnitType(CryptoniaBaseTest):
    def test_get_fiat_currency_and_price_and_unit_type_zero(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_0")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 485.0)
        self.assertEqual(unit_type, "112g")

    def test_get_fiat_currency_and_price_and_unit_type_one(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_1")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 87.21)
        self.assertEqual(unit_type, "Order")

    def test_get_fiat_currency_and_price_and_unit_type_two(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_2")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 240.0)
        self.assertEqual(unit_type, "ORDER")

    def test_get_fiat_currency_and_price_and_unit_type_three(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_3")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 202.13)
        self.assertEqual(unit_type, "50g")

    def test_get_fiat_currency_and_price_and_unit_type_four(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_4")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 4.43)
        self.assertEqual(unit_type, "Each")

    def test_get_fiat_currency_and_price_and_unit_type_five(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_5")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 9.99)
        self.assertEqual(unit_type, "Each")

    def test_get_fiat_currency_and_price_and_unit_type_six(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_6")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 9.99)
        self.assertEqual(unit_type, "Each")

    def test_get_fiat_currency_and_price_and_unit_type_seven(self):
        soup_html = self._get_page_as_soup_html(file_name=f"listings/saved_cryptonia_listing_7")
        fiat_currency, price, unit_type = scrapingFunctions.get_fiat_currency_and_price_and_unit_type(soup_html)

        self.assertEqual(fiat_currency, "USD")
        self.assertEqual(price, 97.0)
        self.assertEqual(unit_type, "item")


class TestGetOriginCountryAndDestinations(CryptoniaBaseTest):

    def test_get_origin_country_and_destinations_zero(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_0")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "United States")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "United States")

    def test_get_origin_country_and_destinations_one(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_1")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "United Kingdom")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "Worldwide")

    def test_get_origin_country_and_destinations_two(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_2")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "United States")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "United States")

    def test_get_origin_country_and_destinations_three(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_3")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "Germany")
        self.assertEqual(len(destination_countries), 10)

        self.assertEqual(destination_countries[0], "Austria")
        self.assertEqual(destination_countries[1], "Belgium")
        self.assertEqual(destination_countries[2], "France")
        self.assertEqual(destination_countries[3], "Finland")
        self.assertEqual(destination_countries[4], "Germany")
        self.assertEqual(destination_countries[5], "Denmark")
        self.assertEqual(destination_countries[6], "Luxembourg")
        self.assertEqual(destination_countries[7], "Poland")
        self.assertEqual(destination_countries[8], "Sweden")
        self.assertEqual(destination_countries[9], "Norway")

    def test_get_origin_country_and_destinations_four(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_4")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "Netherlands")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "Worldwide")

    def test_get_origin_country_and_destinations_five(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_5")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "Worldwide")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "Worldwide")

    def test_get_origin_country_and_destinations_six(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_6")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "Worldwide")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "Worldwide")

    def test_get_origin_country_and_destinations_seven(self):
        soup_html = self._get_page_as_soup_html(file_name="listings/saved_cryptonia_listing_7")
        origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)

        self.assertEqual(origin_country, "Worldwide")
        self.assertEqual(len(destination_countries), 1)

        self.assertEqual(destination_countries[0], "Worldwide")


class TestSupportsEscrow(CryptoniaBaseTest):

    def test_supports_escrow_zero(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_0')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, True)

    def test_supports_escrow_one(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_1')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, False)

    def test_supports_escrow_two(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_2')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, True)

    def test_supports_escrow_three(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_3')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, True)

    def test_supports_escrow_four(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_4')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, False)

    def test_supports_escrow_five(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_5')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, True)

    def test_supports_escrow_six(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_6')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, True)

    def test_supports_escrow_seven(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_7')
        supports_escrow = scrapingFunctions.supports_escrow(soup_html)
        self.assertEqual(supports_escrow, True)


class TestGetQuantityInStockAndUnitType(CryptoniaBaseTest):

    def test_get_quantity_in_stock_and_unit_type_zero(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_0')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 17)
        self.assertEqual(unit_type, "112g")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_one(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_1')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 99)
        self.assertEqual(unit_type, "Order")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_two(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_2')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 1000)
        self.assertEqual(unit_type, "ORDER")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_three(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_3')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 100)
        self.assertEqual(unit_type, "50g")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_four(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_4')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 49415)
        self.assertEqual(unit_type, "Each")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_five(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_5')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 1)
        self.assertEqual(unit_type, "Each")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_six(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_6')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 1)
        self.assertEqual(unit_type, "Each")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_seven(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_7')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(quantity, 9)
        self.assertEqual(unit_type, "item")
        self.assertEqual(minimum_order_unit_amount, 1)

    def test_get_quantity_in_stock_and_unit_type_ten(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_10')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(2000, quantity)
        self.assertEqual("$400", unit_type)
        self.assertEqual(100, minimum_order_unit_amount)

    def test_get_quantity_in_stock_and_unit_type_eleven(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_11')
        quantity, unit_type, minimum_order_unit_amount = \
            scrapingFunctions.get_quantity_in_stock_unit_type_and_minimum_order_unit_amount(
                soup_html)
        self.assertEqual(0, quantity)
        self.assertEqual("gram", unit_type)
        self.assertEqual(28, minimum_order_unit_amount)


class TestGetListingType(CryptoniaBaseTest):

    def test_get_quantity_in_stock_and_unit_type(self):
        for i in range(0, 5):
            soup_html = self._get_page_as_soup_html(file_name=f'listings/saved_cryptonia_listing_{i}')
            listing_type = scrapingFunctions.get_listing_type(soup_html)
            self.assertEqual(listing_type, "Physical Listing")

    def test_get_quantity_in_stock_and_unit_type_five(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_5')
        listing_type = scrapingFunctions.get_listing_type(soup_html)
        self.assertEqual(listing_type, "Digital Autoshop Listing")

    def test_get_quantity_in_stock_and_unit_type_six(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_6')
        listing_type = scrapingFunctions.get_listing_type(soup_html)
        self.assertEqual(listing_type, "Digital Autoshop Listing")

    def test_get_quantity_in_stock_and_unit_type_seven(self):
        soup_html = self._get_page_as_soup_html(file_name='listings/saved_cryptonia_listing_7')
        listing_type = scrapingFunctions.get_listing_type(soup_html)
        self.assertEqual(listing_type, "Digital Listing (Manual Fulfillment)")


class TestGetShippingMethods(CryptoniaBaseTest):

    def test_get_shipping_methods_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_0')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 2

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(["Priority Mail", "Add On"], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([16.0, 0.0], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_1')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 5

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['1st Class Post UK', 'Special Delivery (N.D. Before 1pm) UK', 'Priority Post Europe',
                          'Tracked/Signed Xpress Europe', 'Special Delivery Saturday Before 1pm UK'],
                         shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([5.11, 6.4, 7.68, 12.81, 12.81], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_two(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_2')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 2

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['PRIORITY SHIPPING 2-3 DAY', 'COMBINED SHIPPING ONLY'], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([84817.64, 0.0], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_three(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_3')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 5

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['(DE) DOMESTIC only (KEIN Tracking), 1-5 Tage', '(DE) PRIO-Brief (MIT Tracking), 1-3 Tage',
                          '(DE) Einschreiben-Einwurf (MIT Tracking), 1-5 Tage',
                          '(DE+EU) Zusatzartikel / additional item',
                          '(EU) Reg. Mail / Recommandé (Track&Sign!), 3-10 days'], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([3.33, 5.55, 7.77, 0.0, 8.32], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_four(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_4')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 1

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['NATIONAL MAIL SERVICE [STEALTH]'], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([5.55], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_five(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_5')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 1

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['AUTOSHOP'], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([0.0], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_six(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_6')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 1

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['AUTOSHOP'], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([0.0], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)

    def test_get_shipping_methods_seven(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_7')
        res = shipping_descriptions, shipping_days, shipping_currencies, shipping_prices, shipping_unit_names, \
              price_is_per_units = scrapingFunctions.get_shipping_methods(soup_html)
        expected_length = 1

        self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

        self.assertEqual(['DIGITAL DELIVERY'], shipping_descriptions)
        self.assertEqual([None] * expected_length, shipping_days)
        self.assertEqual(["USD"] * expected_length, shipping_currencies)
        self.assertEqual([0.0], shipping_prices)
        self.assertEqual([None] * expected_length, shipping_unit_names)
        self.assertEqual([False] * expected_length, price_is_per_units)


class TestGetBulkPrices(CryptoniaBaseTest):

    def test_get_bulk_prices(self):
        for i in [*range(0, 4), *range(5, 8)]:
            soup_html = self._get_page_as_soup_html(f'listings/saved_cryptonia_listing_{i}')
            res = \
                scrapingFunctions.get_bulk_prices(
                    soup_html)

            expected_length = 0
            self.assertEqual([len(res[i]) for i in range(len(res))], [expected_length for _ in res])

    def test_get_bulk_prices_four(self):
        soup_html = self._get_page_as_soup_html('listings/saved_cryptonia_listing_4')
        bulk_lower_bounds, bulk_upper_bounds, bulk_fiat_prices, bulk_btc_prices, bulk_discount_percents = \
            scrapingFunctions.get_bulk_prices(
                soup_html)

        same_length_res = [bulk_lower_bounds, bulk_fiat_prices, bulk_btc_prices, bulk_discount_percents]
        expected_length = 10

        self.assertEqual([len(same_length_res[i]) for i in range(len(same_length_res))],
                         [expected_length for _ in same_length_res])

        self.assertEqual(
            [0.0002905, 0.00023217, 0.00020883, 0.00016917, 0.00016217, 0.00015633, 0.000133, 0.00012133, 0.00011667,
             0.000112], bulk_btc_prices)
        self.assertEqual(['38', '50', '55', '64', '65', '66', '71', '74', '75', '76'], bulk_discount_percents)
        self.assertEqual([2.76, 2.21, 1.98, 1.61, 1.54, 1.48, 1.26, 1.15, 1.11, 1.06], bulk_fiat_prices)
        self.assertEqual([5, 10, 25, 50, 75, 100, 250, 500, 750, 1000], bulk_lower_bounds)
        self.assertEqual([9, 24, 49, 74, 99, 249, 499, 749, 999, None], bulk_upper_bounds)


class TestGetSellerAboutDescription(CryptoniaBaseTest):

    def test_get_seller_about_description_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        seller_description = scrapingFunctions.get_seller_about_description(soup_html)
        expected_value = self._get_expected_value('user_profile_0_description', bytes=False)
        self.assertEqual(expected_value, seller_description)

    def test_get_seller_about_description_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        seller_description = scrapingFunctions.get_seller_about_description(soup_html)
        self.assertEqual("This user has not setup his/her profile yet. This is a new feature so please be patient.",
                         seller_description)

    def test_get_seller_about_description_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        seller_description = scrapingFunctions.get_seller_about_description(soup_html)
        expected_value = self._get_expected_value('user_profile_2_description', bytes=False)
        self.assertEqual(expected_value, seller_description)

    def test_get_seller_about_description_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        seller_description = scrapingFunctions.get_seller_about_description(soup_html)
        expected_value = self._get_expected_value('user_profile_3_description', bytes=False)
        self.assertEqual(expected_value, seller_description)

    def test_get_seller_about_description_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        seller_description = scrapingFunctions.get_seller_about_description(soup_html)
        expected_value = self._get_expected_value('user_profile_4_description', bytes=False)
        self.assertEqual(expected_value, seller_description)

    def test_get_seller_about_description_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        seller_description = scrapingFunctions.get_seller_about_description(soup_html)
        expected_value = self._get_expected_value('user_profile_5_description', bytes=False)
        self.assertEqual(expected_value, seller_description)


class TestGetSellerInfo(CryptoniaBaseTest):

    def test_get_seller_info_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)  # TODO: Check vendorPython2 for value on login more than x days ago

        self.assertEqual(96.87, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([('DREAM_MARKET', 34000, 4.82, 5.0, None, None, None, None),
                          ('WALL_STREET_MARKET', 354, 4.7, 5.0, None, None, None, None),
                          ('ALPHA_BAY_MARKET', None, None, None, 9888, 44, 57, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.06925569, 'USD', 646.22), amount_on_escrow)
        self.assertEqual("United Kingdom", ships_from)
        self.assertListEqual(["Worldwide"], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(True, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-15 13:19:58"), member_since)

    def test_get_seller_info_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(0.0, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([], external_market_ratings)
        self.assertEqual(('BTC', 0.0, 'USD', 0.0), amount_on_escrow)
        self.assertEqual(None, ships_from)
        self.assertListEqual(["Worldwide"], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(False, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-10-28 12:43:10"), member_since)

    def test_get_seller_info_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(100.0, percent_positive_rating)
        self.assertTupleEqual((1, 1), disputes)
        self.assertEqual([('DREAM_MARKET', 3700, 4.96, 5.0, None, None, None, 'nr of sales is lower estimate'),
                          ('WALL_STREET_MARKET', 910, 4.93, 5.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 1.07896587, 'USD', 9815.02), amount_on_escrow)
        self.assertEqual("Germany", ships_from)
        self.assertListEqual(
            ['Austria', 'Belgium', 'France', 'Finland', 'Germany', 'Denmark', 'Luxembourg', 'Poland', 'Sweden',
             'Norway'], ships_to)
        self.assertEqual('horch@xabber.de', jabber_id)
        self.assertEqual(True, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-22 10:20:33"), member_since)

    def test_get_seller_info_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
              jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)
        expected_value = self._get_expected_value("user_profile_3_seller_info")

        self.assertTupleEqual(expected_value[:-1], res[:-1])

    def test_get_seller_info_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
              jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)
        expected_value = self._get_expected_value("user_profile_4_seller_info")

        self.assertTupleEqual(expected_value[:-1], res[:-1])

    def test_get_seller_info_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
              jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)
        expected_value = self._get_expected_value("user_profile_5_seller_info")

        self.assertTupleEqual(expected_value[:-1], res[:-1])

    def test_get_seller_info_six(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_6')
        res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
              jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)
        expected_value = self._get_expected_value("user_profile_6_seller_info")

        self.assertTupleEqual(expected_value[:-1], res[:-1])

    def test_get_seller_info_seven(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_7')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(75.0, percent_positive_rating)
        self.assertTupleEqual((2, 2), disputes)
        self.assertListEqual([('EMPIRE_MARKET', 58, 96.67, 100.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.0966432, 'USD', 900.01), amount_on_escrow)
        self.assertEqual("China", ships_from)
        self.assertListEqual(
            ['Worldwide'], ships_to)
        self.assertEqual('cindicator@xmpp.jp', jabber_id)
        self.assertEqual(False, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-05-21 09:11:42"), member_since)

    def test_get_seller_info_eight(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_8')
        res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
              jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)
        expected_value = self._get_expected_value("user_profile_8_seller_info")

        self.assertTupleEqual(expected_value[:-1], res[:-1])

    def test_get_seller_info_nine(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_9')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(98.39, percent_positive_rating)
        self.assertTupleEqual((1, 1), disputes)
        self.assertListEqual([('DREAM_MARKET', 31000, 4.87, 5.0, None, None, None, None),
                              ('ALPHA_BAY_MARKET', None, None, None, 866, 41, 20, None),
                              ('HANSA_MARKET', None, None, None, 1399, 47, 47, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.00257843, 'USD', 23.65), amount_on_escrow)
        self.assertEqual("Worldwide", ships_from)
        self.assertListEqual(["Worldwide"], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(False, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-05-13 07:15:51"), member_since)

    def test_get_seller_info_ten(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_10')
        res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
              jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)
        expected_value = self._get_expected_value("user_profile_10_seller_info")

        self.assertTupleEqual(expected_value[:-1], res[:-1])

    def test_get_seller_info_eleven(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_11')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(100.0, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([], external_market_ratings)
        self.assertEqual(('BTC', 0.00268991, 'USD', 24.69), amount_on_escrow)
        self.assertEqual("Netherlands", ships_from)
        self.assertListEqual(
            ['Worldwide'], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(False, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-23 09:57:45"), member_since)

    def test_get_seller_info_twelve(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_12')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(100.0, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([('DREAM_MARKET', 1000, 4.94, 5.0, None, None, None, None),
                          ('WALL_STREET_MARKET', 1084, 4.68, 5.0, None, None, None, None),
                          ('ALPHA_BAY_MARKET', None, None, None, 168, 3, 0, None),
                          ('HANSA_MARKET', 1000, 4.94, 5.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.15362283, 'USD', 1409.9), amount_on_escrow)
        self.assertEqual("United Kingdom", ships_from)
        self.assertListEqual(
            ['United Kingdom'], ships_to)
        self.assertEqual('martell@jabber.ccc.de', jabber_id)
        self.assertEqual(True, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-21 12:25:03"), member_since)

    def test_get_seller_info_thirteen(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_13')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(100.0, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([('DREAM_MARKET', 3300, 4.97, None, None, None, None, None),
                          ('WALL_STREET_MARKET', 112, 4.86, None, None, None, None, None),
                          ('EMPIRE_MARKET', 27, 100.0, 100.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.0254694, 'USD', 233.06), amount_on_escrow)
        self.assertEqual("Australia", ships_from)
        self.assertListEqual(
            ['Australia'], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(True, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-20 23:27:29"), member_since)

    def test_get_seller_info_fourteen(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_14')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(0.0, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([('DREAM_MARKET', 185, 4.99, 5.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.0, 'USD', 0.0), amount_on_escrow)
        self.assertEqual("United Kingdom", ships_from)
        self.assertListEqual(
            ['Worldwide'], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(False, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-28 20:12:09"), member_since)

    def test_get_seller_info_fifteen(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_15')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(100.0, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([('DREAM_MARKET', 1650, 4.89, 5.0, None, None, None, None),
                          ('WALL_STREET_MARKET', 153, 4.85, 5.0, None, None, None, None),
                          ('EMPIRE_MARKET', 80, 100.0, 100.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.05019241, 'USD', 459.3), amount_on_escrow)
        self.assertEqual("Netherlands", ships_from)
        self.assertListEqual(
            ['Worldwide'], ships_to)
        self.assertEqual(None, jabber_id)
        self.assertEqual(True, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-02 19:35:02"), member_since)

    def test_get_seller_info_sixteen(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_16')
        percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to, \
        jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
            soup_html)

        self.assertEqual(97.87, percent_positive_rating)
        self.assertTupleEqual((0, 0), disputes)
        self.assertEqual([('DREAM_MARKET', 12000, 4.94, 5.0, None, None, None, None),
                          ('BLACK_BANK_MARKET', None, None, None, 4, 0, 0, None),
                          ('NUCLEUS_MARKET', 895, 4.95, 5.0, None, None, None, None),
                          ('ALPHA_BAY_MARKET', None, None, None, 1142, 21, 92, None),
                          ('ABRAXAS_MARKET', 1020, 5.0, 5.0, None, None, None, None),
                          ('MIDDLE_EARTH_MARKET', 145, 9.85, 10.0, None, None, None, None)], external_market_ratings)
        self.assertEqual(('BTC', 0.03794626, 'USD', 347.33), amount_on_escrow)
        self.assertEqual("United States", ships_from)
        self.assertListEqual(
            ['United States'], ships_to)
        self.assertEqual('MarleysMainMan@xmpp.jp', jabber_id)
        self.assertEqual(True, fe_enabled)
        self.assertEqual(datetime.fromisoformat("2019-04-02 18:48:33"), member_since)


class TestGetParenthesisNumberAndVendorLevel(CryptoniaBaseTest):

    def test_get_parenthesis_number_and_vendor_level_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(1490, parenthesis_number)
        self.assertEqual(1, vendor_level)

    def test_get_parenthesis_number_and_vendor_level_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(0, parenthesis_number)
        self.assertEqual(0, vendor_level)

    def test_get_parenthesis_number_and_vendor_level_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(683, parenthesis_number)
        self.assertEqual(2, vendor_level)

    def test_get_parenthesis_number_and_vendor_level_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(3, parenthesis_number)
        self.assertEqual(1, vendor_level)

    def test_get_parenthesis_number_and_vendor_level_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(133, parenthesis_number)
        self.assertEqual(1, vendor_level)

    def test_get_parenthesis_number_and_vendor_level_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(8, parenthesis_number)
        self.assertEqual(1, vendor_level)

    def test_get_parenthesis_number_and_vendor_level_six(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_6')
        parenthesis_number, vendor_level = scrapingFunctions.get_parenthesis_number_and_vendor_level(soup_html)

        self.assertEqual(2, parenthesis_number)
        self.assertEqual(1, vendor_level)


class TestGetFeedbacks(CryptoniaBaseTest):

    def test_get_feedbacks_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        expected_value = tuple(self._get_expected_value('user_profile_0_feedback'))
        self.assertTupleEqual(expected_value, feedbacks)

    def test_get_feedbacks_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        expected_value = tuple(self._get_expected_value('user_profile_1_feedback'))

        self.assertTupleEqual(expected_value, feedbacks)

    def test_get_feedbacks_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        expected_value = tuple(self._get_expected_value('user_profile_2_feedback'))

        self.assertTupleEqual(expected_value, feedbacks)

    def test_get_feedbacks_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        expected_value = tuple(self._get_expected_value('user_profile_3_feedback'))

        self.assertTupleEqual(expected_value, feedbacks)

    def test_get_feedbacks_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        expected_value = tuple(self._get_expected_value('user_profile_4_feedback'))

        self.assertTupleEqual(expected_value, feedbacks)

    def test_get_feedbacks_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        expected_value = tuple(self._get_expected_value('user_profile_5_feedback'))

        self.assertTupleEqual(expected_value, feedbacks)


class TestGetNextFeedbackUrl(CryptoniaBaseTest):

    def test_get_next_feedback_url_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual('/user/terrysukstock/2#feedback', next_feedback_url)

    def test_get_next_feedback_url_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual(None, next_feedback_url)

    def test_get_next_feedback_url_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual('/user/GreenSupreme/2#feedback', next_feedback_url)

    def test_get_next_feedback_url_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual(None, next_feedback_url)

    def test_get_next_feedback_url_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual('/user/Raux18faux/2#feedback', next_feedback_url)

    def test_get_next_feedback_url_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual(None, next_feedback_url)

    def test_get_next_feedback_url_eight(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_8')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual(None, next_feedback_url)

    def test_get_next_feedback_url_nine(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_9')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual("/user/TheShop/2#feedback", next_feedback_url)

    def test_get_next_feedback_url_ten(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_10')
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual("/user/pornseller/3#feedback", next_feedback_url)


class TestGetPGPKey(CryptoniaBaseTest):

    def test_get_pgp_key_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_0_pgp_key', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, pgp_key)

    def test_get_pgp_key_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_1_pgp_key', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, pgp_key)

    def test_get_pgp_key_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_2_pgp_key', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, pgp_key)

    def test_get_pgp_key_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_3_pgp_key', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, pgp_key)

    def test_get_pgp_key_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_4_pgp_key', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, pgp_key)

    def test_get_pgp_key_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_5_pgp_key', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, pgp_key)


class TestGetTermsAndConditions(CryptoniaBaseTest):

    def test_get_terms_and_conditions_zero(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_0')
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_0_terms_and_conditions', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, terms_and_conditions)

    def test_get_terms_and_conditions_one(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_1')
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_1_terms_and_conditions', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, terms_and_conditions)

    def test_get_terms_and_conditions_two(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_2')
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_2_terms_and_conditions', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, terms_and_conditions)

    def test_get_terms_and_conditions_three(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_3')
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_3_terms_and_conditions', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, terms_and_conditions)

    def test_get_terms_and_conditions_four(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_4')
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_4_terms_and_conditions', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, terms_and_conditions)

    def test_get_terms_and_conditions_five(self):
        soup_html = self._get_page_as_soup_html('users/saved_cryptonia_user_profile_5')
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        expected_value = self._get_expected_value(file_name='user_profile_5_terms_and_conditions', bytes=False)
        expected_value = expected_value if not expected_value == "" else None
        self.assertEqual(expected_value, terms_and_conditions)


class TestGetLoginPayload(CryptoniaBaseTest):

    def test_get_login_payload(self):
        soup_html = self._get_page_as_soup_html('login_page/saved_cryptonia_login_page')
        username = "034q8jwfrsejnjj"
        password = "dsfghw49fhsvndfj"
        captcha_solution = "uajnh"
        login_payload = scrapingFunctions.get_login_payload(soup_html, username, password, captcha_solution)

        keys = [key for key in login_payload.keys()]

        self.assertTupleEqual((keys[0], login_payload[keys[0]]), ('username', username))
        self.assertTupleEqual((keys[1], login_payload[keys[1]]), ('password', password))
        self.assertTupleEqual((keys[2], login_payload[keys[2]]), ('captcha', captcha_solution))
        self.assertEqual(keys[3], 'sess_code')
        self.assertTupleEqual((keys[4], login_payload[keys[4]]), ('submit', "LOGIN"))


class TestGetCaptchaImageUrl(CryptoniaBaseTest):

    def test_get_captcha_image_url(self):
        soup_html = self._get_page_as_soup_html('login_page/saved_cryptonia_login_page')
        image_url = scrapingFunctions.get_captcha_image_url(soup_html)
        self.assertEqual("/captcha", image_url)


class TestGetMetaRefreshInterval(CryptoniaBaseTest):

    def test_get_meta_refresh_interval(self):
        soup_html = self._get_page_as_soup_html('ddos/anti_ddos_page')
        wait_interval, redirect_url = scrapingFunctions.get_meta_refresh_interval(soup_html)
        self.assertEqual(2, wait_interval)
        self.assertEqual(redirect_url, "/login")

    # def test_temp(self):
    #     rng = [3,4,5,6,8,10]
    #     for i in rng:
    #         soup_html = self._get_page_as_soup_html(f'users/saved_cryptonia_user_profile_{i}')
    #         res = percent_positive_rating, disputes, external_market_ratings, amount_on_escrow, ships_from, ships_to,\
    #               jabber_id, fe_enabled, member_since, last_online = scrapingFunctions.get_seller_info(
    #             soup_html)
    #         with open(f'/home/magnus/PycharmProjects/msc/tests/cryptonia/expected_values/user_profile_{
    # i}_seller_info', 'wb') as f:  # Python 3: open(..., 'wb')
    #             f.write(pickle.dumps(res)) if res else f.write(b"")
