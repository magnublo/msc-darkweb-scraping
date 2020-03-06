from unittest import TestCase

from src.dream.dream_scrape import get_usd_price_from_rates, process_shipping_methods

RATES = {'BTC': 1.0, 'mBTC': 1000.0, 'BCH': 8.9, 'XMR': 32.4, 'USD': 11423.0, 'EUR': 9245.2, 'GBP': 8228.2,
         'CAD': 14413.3, 'AUD': 14515.0, 'mBCH': 8942.0, 'SEK': 91740.4, 'NOK': 90048.5, 'DKK': 68886.2,
         'TRY': 43591.2, 'CNH': 72649.0, 'HKD': 90344.3, 'RUB': 654063.0, 'INR': 738407.2, 'JPY': 1228515.4}


class TestGetUsdPriceFromRates(TestCase):

    def test_get_usd_price_from_rates(self):
        usd_price = get_usd_price_from_rates(5, "EUR", RATES)
        self.assertEqual(6.177800372084973, usd_price)


class TestProcessShippingMethods(TestCase):

    def test_process_shipping_methods_zero(self):
        shipping_methods = process_shipping_methods((('Private Message', None, 'BTC', 0.0, None, None),), RATES)
        self.assertTupleEqual((('Private Message', None, 'USD', 0.0, None, None),), shipping_methods)

    def test_process_shipping_methods_one(self):
        # noinspection PyTypeChecker
        shipping_methods = process_shipping_methods((('DHL or EMS (Leave phone number for delivery company)', None,
                                                      'BTC', 0.00214, None, None), (
                                                         'Second item ordered free shipping', None, 'BTC', 0.0, None,
                                                         None)), RATES)
        self.assertTupleEqual((('DHL or EMS (Leave phone number for delivery company)', None, 'USD', 24.44522, None,
                                None), ('Second item ordered free shipping', None, 'USD', 0.0, None, None)),
                              shipping_methods)

    def test_process_shipping_methods_two(self):
        # noinspection PyTypeChecker
        shipping_methods = process_shipping_methods((('EXPRESS TRACKED TO EUROPE', None, 'BTC', 0.0025127, None, None),
                                                     ('EXPRESS TRACKED TO USA AND REST OF THE WORLD', None, 'BTC',
                                                      0.0034437, None, None)), RATES)
        self.assertTupleEqual((('EXPRESS TRACKED TO EUROPE', None, 'USD', 28.7025721, None, None),
                               ('EXPRESS TRACKED TO USA AND REST OF THE WORLD', None, 'USD', 39.3373851, None, None)),
                              shipping_methods)
