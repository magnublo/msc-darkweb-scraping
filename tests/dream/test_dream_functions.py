import os
from typing import Dict

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
