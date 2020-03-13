import datetime
import os
from typing import Dict, Tuple

from bs4 import BeautifulSoup

from definitions import ROOT_DIR
from tests.dream.dream_base_test import DreamBaseTest
from src.dream.dream_functions import DreamScrapingFunctions as scrapingFunctions


class TestGetSellerNameFromListing(DreamBaseTest):

    def test_get_seller_name_from_listing(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        seller_name: str = scrapingFunctions.get_seller_name_from_listing(soup_html)
        self.assertEqual("PHARMORA", seller_name)


class TestAcceptsCurrencies(DreamBaseTest):

    def test_accepts_currencies_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0.html")
        btc, bch, xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual((True, True, False), (btc, bch, xmr))

    def test_accepts_currencies_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1.html")
        btc, bch, xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual((True, True, True), (btc, bch, xmr))

    def test_accepts_currencies_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2.html")
        btc, bch, xmr = scrapingFunctions.accepts_currencies(soup_html)
        self.assertEqual((True, True, True), (btc, bch, xmr))


class TestGetFiatExchangeRates(DreamBaseTest):

    def test_get_fiat_exchange_rates_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0.html")
        rates: Dict[str, float] = scrapingFunctions.get_fiat_exchange_rates(soup_html)
        self.assertDictEqual(
            {'BTC': 1.0, 'mBTC': 1000.0, 'BCH': 15.3, 'USD': 5261.1, 'EUR': 4603.8, 'GBP': 4014.5, 'CAD': 6914.9,
             'AUD': 7269.4, 'mBCH': 15347.0, 'BRL': 19824.1, 'DKK': 34344.7, 'NOK': 43971.3, 'SEK': 47511.7,
             'TRY': 28350.5, 'CNH': 36462.4, 'HKD': 41291.9, 'RUB': 348511.4, 'INR': 384973.9, 'JPY': 597041.0}, rates)

    def test_get_fiat_exchange_rates_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1.html")
        rates: Dict[str, float] = scrapingFunctions.get_fiat_exchange_rates(soup_html)
        self.assertDictEqual(
            {'BTC': 1.0, 'mBTC': 1000.0, 'BCH': 8.9, 'XMR': 32.4, 'USD': 11423.0, 'EUR': 9245.2, 'GBP': 8228.2,
             'CAD': 14413.3, 'AUD': 14515.0, 'mBCH': 8942.0, 'SEK': 91740.4, 'NOK': 90048.5, 'DKK': 68886.2,
             'TRY': 43591.2, 'CNH': 72649.0, 'HKD': 90344.3, 'RUB': 654063.0, 'INR': 738407.2, 'JPY': 1228515.4}, rates)

    def test_get_fiat_exchange_rates_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2.html")
        rates: Dict[str, float] = scrapingFunctions.get_fiat_exchange_rates(soup_html)
        self.assertDictEqual(
            {'BTC': 1.0, 'mBTC': 1000.0, 'BCH': 8.9, 'XMR': 32.4, 'USD': 11423.0, 'EUR': 9245.2, 'GBP': 8228.2,
             'CAD': 14413.3, 'AUD': 14515.0, 'mBCH': 8942.0, 'SEK': 91740.4, 'NOK': 90048.5, 'DKK': 68886.2,
             'TRY': 43591.2, 'CNH': 72649.0, 'HKD': 90344.3, 'RUB': 654063.0, 'INR': 738407.2, 'JPY': 1228515.4}, rates)


class TestGetOriginCountry(DreamBaseTest):

    def test_get_origin_country_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0.html")
        origin_country = scrapingFunctions.get_origin_country(soup_html)
        self.assertEqual("United States", origin_country)

    def test_get_origin_country_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1.html")
        origin_country = scrapingFunctions.get_origin_country(soup_html)
        self.assertEqual("Worldwide", origin_country)

    def test_get_origin_country_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2.html")
        origin_country = scrapingFunctions.get_origin_country(soup_html)
        self.assertEqual("Worldwide", origin_country)


class TestGetDestinationCountries(DreamBaseTest):

    def test_get_destination_countries_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0.html")
        destination_countries = scrapingFunctions.get_destination_countries(soup_html)
        self.assertTupleEqual(('United States', 'Worldwide'), destination_countries)

    def test_get_destination_countries_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1.html")
        destination_countries = scrapingFunctions.get_destination_countries(soup_html)
        self.assertTupleEqual(('Worldwide', 'Worldwide'), destination_countries)

    def test_get_destination_countries_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2.html")
        destination_countries = scrapingFunctions.get_destination_countries(soup_html)
        self.assertTupleEqual(('Worldwide', 'Worldwide'), destination_countries)


class TestGetHasEscrow(DreamBaseTest):

    def test_get_has_escrow_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0.html")
        supports_escrow = scrapingFunctions.get_has_escrow(soup_html)
        self.assertEqual(True, supports_escrow)

    def test_get_has_escrow_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1.html")
        supports_escrow = scrapingFunctions.get_has_escrow(soup_html)
        self.assertEqual(False, supports_escrow)

    def test_get_has_escrow_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2.html")
        supports_escrow = scrapingFunctions.get_has_escrow(soup_html)
        self.assertEqual(True, supports_escrow)


class TestGetPriceAndCurrency(DreamBaseTest):

    def test_get_price_and_currency_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        price_and_currency = scrapingFunctions.get_price_and_currency(soup_html)
        self.assertTupleEqual((50.96, 'USD'), price_and_currency)

    def test_get_price_and_currency_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        price_and_currency = scrapingFunctions.get_price_and_currency(soup_html)
        self.assertTupleEqual((0.000787, 'BTC'), price_and_currency)

    def test_get_price_and_currency_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2")
        price_and_currency = scrapingFunctions.get_price_and_currency(soup_html)
        self.assertTupleEqual((50.96, 'USD'), price_and_currency)


class TestGetShippingMethods(DreamBaseTest):

    def test_get_shipping_methods_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('EMS-12 to 14 Working Days', None, 'USD', 25.0, None, None), (
            'Free Shipping For Multiple Orders Only Select If You Have Already Paid In Your Other Order!', None, 'USD',
            0.0,
            None, None)), shipping_methods)

    def test_get_shipping_methods_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((), shipping_methods)

    def test_get_shipping_methods_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual(('Private Message', None, 'BTC', 0.0, None, None), shipping_methods)

    def test_get_shipping_methods_three(self):
        soup_html = self._get_page_as_soup_html("listings/listing_3")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('DHL or EMS (Leave phone number for delivery company)', None, 'BTC', 0.00214, None,
                                None), ('Second item ordered free shipping', None, 'BTC', 0.0, None, None)),
                              shipping_methods)

    def test_get_shipping_methods_four(self):
        soup_html = self._get_page_as_soup_html("listings/listing_4")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('EXPRESS TRACKED TO EUROPE', None, 'BTC', 0.0025127, None, None),
                               ('EXPRESS TRACKED TO USA AND REST OF THE WORLD', None, 'BTC', 0.0034437, None, None)),
                              shipping_methods)


class TestGetListingTitle(DreamBaseTest):

    def test_get_listing_title_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        title = scrapingFunctions.get_listing_title(soup_html)
        self.assertEqual("☢100 PILLS X Soma 350mg $49☢", title)

    def test_get_listing_title_three(self):
        soup_html = self._get_page_as_soup_html("listings/listing_3")
        title = scrapingFunctions.get_listing_title(soup_html)
        self.assertEqual("Louis Vuitton Bracelet 48 AAA+", title)


class TestGetListingText(DreamBaseTest):

    def test_get_listing_text_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        listing_text = scrapingFunctions.get_listing_text(soup_html)
        self.assertTrue(len(listing_text) > 0)

    def test_get_listing_text_three(self):
        soup_html = self._get_page_as_soup_html("listings/listing_3")
        listing_text = scrapingFunctions.get_listing_text(soup_html)
        self.assertEqual("Louis Vuitton Bracelet 48 ", listing_text)


class TestGetCategories(DreamBaseTest):

    def test_get_categories_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        listing_categories = scrapingFunctions.get_categories(soup_html)
        self.assertTupleEqual((('Drugs', 104, None, 0),), listing_categories)

    def test_get_categories_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        listing_categories = scrapingFunctions.get_categories(soup_html)
        self.assertTupleEqual((('Software', 118, 'Digital Goods', 1), ('Digital Goods', 103, None, 0)),
                              listing_categories)

    def test_get_categories_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2")
        listing_categories = scrapingFunctions.get_categories(soup_html)
        self.assertTupleEqual((('Information', 115, 'Digital Goods', 1), ('Digital Goods', 103, None, 0)),
                              listing_categories)

    def test_get_categories_three(self):
        soup_html = self._get_page_as_soup_html("listings/listing_3")
        listing_categories = scrapingFunctions.get_categories(soup_html)
        self.assertTupleEqual((('Jewellery', 137, 'Other', 1), ('Other', 107, None, 0)),
                              listing_categories)

    def test_get_categories_four(self):
        soup_html = self._get_page_as_soup_html("listings/listing_4")
        listing_categories = scrapingFunctions.get_categories(soup_html)
        self.assertTupleEqual(
            (('Accessories', 192, 'Counterfeits', 2), ('Counterfeits', 135, 'Other', 1), ('Other', 107, None, 0)),
            listing_categories)

    def test_get_categories_five(self):
        soup_html = self._get_page_as_soup_html("listings/listing_5")
        listing_categories = scrapingFunctions.get_categories(soup_html)
        self.assertTupleEqual(
            (('Speed', 190, 'Stimulants', 2), ('Stimulants', 129, 'Drugs', 1), ('Drugs', 104, None, 0)),
            listing_categories)


class TestGetSellerName(DreamBaseTest):

    def test_get_seller_name_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0.html")
        name = scrapingFunctions.get_seller_name(soup_html)
        self.assertEqual("JoyInc", name)

    def test_get_seller_name_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1.html")
        name = scrapingFunctions.get_seller_name(soup_html)
        self.assertEqual("Antonio777", name)

    def test_get_seller_name_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2.html")
        name = scrapingFunctions.get_seller_name(soup_html)
        self.assertEqual("amsterdamsupply", name)

    def test_get_seller_name_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3.html")
        name = scrapingFunctions.get_seller_name(soup_html)
        self.assertEqual("ChefRamsay", name)


class TestGetExternalMarketRatings(DreamBaseTest):

    def test_get_external_market_ratings_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        external_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_ratings)

    def test_get_external_market_ratings_seven(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_7")
        external_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((('ALPHA_BAY_MARKET', None, None, None, 402, 5, 2, None),
                               ('HANSA_MARKET', None, None, None, 7, 0, 0, None)), external_ratings)


class TestGetFiatExchangeRatesFromSellerPage(DreamBaseTest):

    def test_get_fiat_exchange_rates_from_seller_page(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        fiat_exchange_rates = scrapingFunctions.get_fiat_exchange_rates_from_seller_page(soup_html)
        self.assertDictEqual(
            {'BTC': 1.0, 'mBTC': 1000.0, 'BCH': 14.0, 'USD': 5517.0, 'EUR': 4835.0, 'GBP': 4216.1, 'CAD': 7262.2,
             'AUD': 7634.5, 'mBCH': 14024.0, 'BRL': 20819.6, 'DKK': 36069.3, 'NOK': 46179.3, 'SEK': 49897.5,
             'TRY': 29774.1, 'CNH': 38293.4, 'HKD': 43365.3, 'RUB': 366011.7, 'INR': 404305.2, 'JPY': 627021.1},
            fiat_exchange_rates)


class TestGetFeedbackRows(DreamBaseTest):

    def test_get_feedback_rows_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        feedback_rows: Tuple[BeautifulSoup] = scrapingFunctions.get_feedback_rows(soup_html)
        self.assertTupleEqual((), feedback_rows)

    def test_get_feedback_rows_seven(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_7")
        feedback_rows: Tuple[BeautifulSoup] = scrapingFunctions.get_feedback_rows(soup_html)
        self.assertTupleEqual((), feedback_rows)

    def test_get_feedback_rows_eight(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_8")
        feedback_rows: Tuple[BeautifulSoup] = scrapingFunctions.get_feedback_rows(soup_html)
        self.assertEqual(len(feedback_rows), 300)


class TestGetFeedbackInfo(DreamBaseTest):

    def test_get_feedback_info_eight(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_8")
        feedback_rows: Tuple[BeautifulSoup] = scrapingFunctions.get_feedback_rows(soup_html)[:4]
        feedback_infos = []
        for feedback_row in feedback_rows:
            feedback_infos.append(scrapingFunctions.get_feedback_info(
                feedback_row))

        self.assertListEqual(
            [(datetime.timedelta(days=3), 5, 'FE for Trust!!!!!! Neurkunde.....', 'ad64e631', 'S...8', 30.0, 'USD'),
             (datetime.timedelta(days=4), 5, 'Enter your comments here', '53f74222', 'B...7', 30.0, 'USD'), (
                 datetime.timedelta(days=1, seconds=79200), 5, 'Schnelle Lieferung und sehr gute QualitÃ¤t', '161042b0',
                 'B...8', 30.0, 'USD'),
             (datetime.timedelta(days=1, seconds=50400), 5, '', 'd41d8cd9', 'k...r', 28.0, 'USD')], feedback_infos)


class TestGetPgpKey(DreamBaseTest):

    def test_get_pgp_key_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        self.assertTrue(len(pgp_key) > 100)

    def test_get_pgp_key_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2")
        pgp_key = scrapingFunctions.get_pgp_key(soup_html)
        self.assertTrue(pgp_key is None)


class TestGetTermsAndConditions(DreamBaseTest):

    def test_get_terms_and_conditions_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        terms_and_conditions = scrapingFunctions.get_terms_and_conditions(soup_html)
        self.assertTrue(len(terms_and_conditions) > 100)


class TestGetNumberOfSalesAndrating(DreamBaseTest):

    def test_get_number_of_sales_and_rating_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        number_of_sales_and_rating = scrapingFunctions.get_number_of_sales_and_rating(soup_html)
        self.assertTupleEqual(number_of_sales_and_rating, (680, 4.96))
