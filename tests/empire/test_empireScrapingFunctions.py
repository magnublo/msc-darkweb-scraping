from unittest import TestCase

from src.empire.empire_functions import EmpireScrapingFunctions as scrapingFunctions
from tests.empire.empire_base_test import EmpireBaseTest


class TestGetProductClassQuantityLeftAndEndsIn(EmpireBaseTest):

    def test_get_product_class_quantity_left_and_ends_in_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_0')
        listing_type, quantity_in_stock, ends_in = scrapingFunctions.get_product_class_quantity_left_and_ends_in(
            soup_html)

        self.assertEqual("Digital", listing_type)
        self.assertEqual(None, quantity_in_stock)
        self.assertEqual("Never", ends_in)

    def test_get_product_class_quantity_left_and_ends_in_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_1')
        listing_type, quantity_in_stock, ends_in = scrapingFunctions.get_product_class_quantity_left_and_ends_in(
            soup_html)

        self.assertEqual("Physical Package", listing_type)
        self.assertEqual(8, quantity_in_stock)
        self.assertEqual("Never", ends_in)


class TestHasUnlimitedDispatch(EmpireBaseTest):

    def test_has_unlimited_dispatch_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_0')
        has_unlimited_dispatch = scrapingFunctions.has_unlimited_dispatch_and_quantity_in_stock(soup_html)
        self.assertEqual((True, None), has_unlimited_dispatch)

    def test_has_unlimited_dispatch_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_1')
        has_unlimited_dispatch = scrapingFunctions.has_unlimited_dispatch_and_quantity_in_stock(soup_html)
        self.assertEqual((False, None), has_unlimited_dispatch)

    def test_has_unlimited_dispatch_six(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_6')
        has_unlimited_dispatch = scrapingFunctions.has_unlimited_dispatch_and_quantity_in_stock(soup_html)
        self.assertEqual((True, 12), has_unlimited_dispatch)


class TestGetDescription(EmpireBaseTest):
    def test_get_description_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_0')
        description = scrapingFunctions.get_description(soup_html)
        expected_value = self._get_expected_value('listing_0_description', bytes=False)
        self.assertEqual(expected_value, description)

    def test_get_description_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_1')
        description = scrapingFunctions.get_description(soup_html)
        expected_value = self._get_expected_value('listing_1_description', bytes=False)
        self.assertEqual(expected_value, description)


class TestGetNrsOfViews(EmpireBaseTest):
    def test_get_nrs_of_views(self):
        soup_html = self._get_page_as_soup_html('search_results/saved_empire_search_result_0')
        nrs_of_views = scrapingFunctions.get_nrs_of_views(soup_html)
        self.assertTupleEqual((18829, 2735, 2594, 2398, 184, 4074, 41084, 510, 3151, 208, 7132, 595, 136, 15447, 533),
                              nrs_of_views)


class TestGetShippingMethods(EmpireBaseTest):
    def test_get_shipping_methods_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_0')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('default', 1, 'USD', 0.0, None, False),), shipping_methods)

    def test_get_shipping_methods_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_1')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('airmail', 8, 'USD', 5.0, 'order', True),), shipping_methods)

    def test_get_shipping_methods_two(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_2')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('UK', 1, 'USD', 0.0, 'order', True), ('EU', 5, 'USD', 0.0, 'order', True),
                               ('WW', 14, 'USD', 0.0, 'order', True)), shipping_methods)

    def test_get_shipping_methods_three(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_3')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('priority', 3, 'USD', 8.0, 'order', True),), shipping_methods)

    def test_get_shipping_methods_four(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_4')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('priority', 3.0, 'USD', 20.0, 'order', True),), shipping_methods)

    def test_get_shipping_methods_five(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_5')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('USPS 2 DAY PRIORITY', 2.0, 'USD', 15.0, 'order', True),), shipping_methods)

    def test_get_shipping_methods_six(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_6')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('default', 1.0, 'USD', 0.0, None, False),), shipping_methods)

    def test_get_shipping_methods_seven(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_7')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('Free', 0.02, 'USD', 0.0, 'order', True),), shipping_methods)

    def test_get_shipping_methods_eight(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_8')
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('free', 0.01, 'USD', 0.0, 'order', True),), shipping_methods)


class TestGetBulkPrices(EmpireBaseTest):

    def test_get_bulk_prices_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_0')
        bulk_prices = scrapingFunctions.get_bulk_prices(soup_html)
        self.assertTupleEqual((), bulk_prices)

    def test_get_bulk_prices_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_1')
        bulk_prices = scrapingFunctions.get_bulk_prices(soup_html)
        self.assertTupleEqual((), bulk_prices)

    def test_get_bulk_prices_two(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_2')
        bulk_prices = scrapingFunctions.get_bulk_prices(soup_html)
        self.assertTupleEqual((), bulk_prices)

    def test_get_bulk_prices_three(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_3')
        bulk_prices = scrapingFunctions.get_bulk_prices(soup_html)
        self.assertTupleEqual(
            ((250, 499, 1.3, 0.00013823, None), (500, 999, 1.0, 0.00010633, None), (1000, 3000, 0.8, 8.506e-05, None)),
            bulk_prices)

    def test_get_bulk_prices_four(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_4')
        bulk_prices = scrapingFunctions.get_bulk_prices(soup_html)
        self.assertTupleEqual(((10000, 14999, 0.7, 7.518e-05, None), (15000, 19000, 0.6, 6.444e-05, None),
                               (20000, 30000, 0.5, 5.37e-05, None)), bulk_prices)


class TestGetCaptchaImageUrlFromMarketPage(EmpireBaseTest):

    def test_get_captcha_image_url_from_market_page(self):
        soup_html = self._get_page_as_soup_html("login_page/saved_empire_login_page_0")
        captcha_image_url = scrapingFunctions.get_captcha_image_url_from_market_page(soup_html)
        self.assertEqual("/public/captchaimg/1569591995.7041.jpg", captcha_image_url)


class TestUserIsBanned(EmpireBaseTest):

    def test_user_is_banned_zero(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_0")
        is_banned = scrapingFunctions.user_is_banned(soup_html)
        self.assertEqual(False, is_banned)

    def test_user_is_banned_one(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_1")
        is_banned = scrapingFunctions.user_is_banned(soup_html)
        self.assertEqual(True, is_banned)

    def test_user_is_banned_two(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_2")
        is_banned = scrapingFunctions.user_is_banned(soup_html)
        self.assertEqual(False, is_banned)

    def test_user_is_banned_three(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_3")
        is_banned = scrapingFunctions.user_is_banned(soup_html)
        self.assertEqual(False, is_banned)


class TestGetCategoryUrlsAndNrOfListings(EmpireBaseTest):
    def test_get_category_urls_and_nr_of_listings(self):
        soup_html = self._get_page_as_soup_html("saved_empire_category_index_0")
        category_urls_and_nrs_of_listings = scrapingFunctions.get_category_urls_and_nr_of_listings(soup_html)
        a = 1


class TestGetExternalMarketRatings(EmpireBaseTest):

    def test_get_external_market_ratings_zero(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_0")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((('DREAM_MARKET', 138, 5.0, None), ('WALL_STREET_MARKET', 89, 4.95, None)),
                              external_market_ratings)

    def test_get_external_market_ratings_one(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_1")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_market_ratings)

    def test_get_external_market_ratings_two(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_2")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((('DREAM_MARKET', 160, 4.81, None),), external_market_ratings)

    def test_get_external_market_ratings_three(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_3")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_market_ratings)

    def test_get_external_market_ratings_four(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_4")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_market_ratings)

    def test_get_external_market_ratings_five(self):
        soup_html = self._get_page_as_soup_html("users/saved_empire_user_5")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((('DREAM_MARKET', 470, 4.92, None),), external_market_ratings)


class TestGetListingCategories(EmpireBaseTest):

    def test_get_listing_categories_zero(self):
        soup_html = self._get_page_as_soup_html("listings/saved_empire_listing_0")
        listing_categories = scrapingFunctions.get_listing_categories(soup_html, "empiremktxgjovhm.onion")
        self.assertTupleEqual((('Digital Products', 5, None, 0), ('Other', 49, 'Digital Products', 1)),
                              listing_categories)
        for category in listing_categories:
            self.assertEqual(category[3], listing_categories.index(category))

    def test_get_listing_categories_one(self):
        soup_html = self._get_page_as_soup_html("listings/saved_empire_listing_1")
        listing_categories = scrapingFunctions.get_listing_categories(soup_html, "empiremktxgjovhm.onion")
        self.assertTupleEqual((('Jewels & Gold', 6, None, 0), ('Gold', 50, 'Jewels & Gold', 1)), listing_categories)
        for category in listing_categories:
            self.assertEqual(category[3], listing_categories.index(category))

    def test_get_listing_categories_two(self):
        soup_html = self._get_page_as_soup_html("listings/saved_empire_listing_2")
        listing_categories = scrapingFunctions.get_listing_categories(soup_html, "empiremktxgjovhm.onion")
        self.assertTupleEqual((('Drugs & Chemicals', 2, None, 0), ('Stimulants', 26, 'Drugs & Chemicals', 1),
                               ('Cocaine', 105, 'Stimulants', 2)), listing_categories)
        for category in listing_categories:
            self.assertEqual(category[3], listing_categories.index(category))

    def test_get_listing_categories_three(self):
        soup_html = self._get_page_as_soup_html("listings/saved_empire_listing_3")
        listing_categories = scrapingFunctions.get_listing_categories(soup_html, "empiremktxgjovhm.onion")
        self.assertTupleEqual(
            (('Drugs & Chemicals', 2, None, 0), ('Benzos', 19, 'Drugs & Chemicals', 1), ('Pills', 69, 'Benzos', 2)),
            listing_categories)
        for category in listing_categories:
            self.assertEqual(category[3], listing_categories.index(category))

    def test_get_listing_categories_four(self):
        soup_html = self._get_page_as_soup_html("listings/saved_empire_listing_4")
        listing_categories = scrapingFunctions.get_listing_categories(soup_html, "empiremktxgjovhm.onion")
        self.assertTupleEqual(
            (('Drugs & Chemicals', 2, None, 0), ('Benzos', 19, 'Drugs & Chemicals', 1), ('Pills', 69, 'Benzos', 2)),
            listing_categories)
        for category in listing_categories:
            self.assertEqual(category[3], listing_categories.index(category))

    def test_get_listing_categories_five(self):
        soup_html = self._get_page_as_soup_html("listings/saved_empire_listing_5")
        listing_categories = scrapingFunctions.get_listing_categories(soup_html, "empiremktxgjovhm.onion")
        self.assertTupleEqual(
            (('Drugs & Chemicals', 2, None, 0), ('Benzos', 19, 'Drugs & Chemicals', 1), ('Pills', 69, 'Benzos', 2)),
            listing_categories)
        for category in listing_categories:
            self.assertEqual(category[3], listing_categories.index(category))


class TestGetLoginPayload(EmpireBaseTest):

    def test_get_login_payload(self):
        soup_html = self._get_page_as_soup_html('login_page/saved_empire_login_page_0')
        login_payload: dict = scrapingFunctions.get_login_payload(soup_html, 'using_python1', 'Password123!', "012371")
        a = 1


class TestGetOriginCountryAndDestinationsAndPaymentType(EmpireBaseTest):

    def test_get_origin_country_and_destinations_and_payment_type_zero(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_0')
        origin_country, destination_countries, payment_type = \
            scrapingFunctions.get_origin_country_and_destinations_and_payment_type(
                soup_html)
        self.assertEqual(origin_country, "World Wide")
        self.assertTupleEqual(('World Wide',), destination_countries)
        self.assertEqual("Escrow", payment_type)

    def test_get_origin_country_and_destinations_and_payment_type_one(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_1')
        origin_country, destination_countries, payment_type = \
            scrapingFunctions.get_origin_country_and_destinations_and_payment_type(
                soup_html)
        self.assertEqual(origin_country, "Latvia")
        self.assertTupleEqual(('World Wide',), destination_countries)
        self.assertEqual("Escrow", payment_type)

    def test_get_origin_country_and_destinations_and_payment_type_nine(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_9')
        origin_country, destination_countries, payment_type = \
            scrapingFunctions.get_origin_country_and_destinations_and_payment_type(
                soup_html)
        self.assertEqual(origin_country, "Germany")
        self.assertTupleEqual(('Austria', 'Belgium', 'Finland', 'France', 'Germany'), destination_countries)
        self.assertEqual("Escrow", payment_type)

    def test_get_origin_country_and_destinations_and_payment_type_ten(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_10')
        origin_country, destination_countries, payment_type = \
            scrapingFunctions.get_origin_country_and_destinations_and_payment_type(
                soup_html)
        self.assertEqual(origin_country, "Netherlands")
        self.assertTupleEqual(('World Wide', 'United States', 'Asia', 'Africa', 'Antarctica(c)'), destination_countries)
        self.assertEqual("Escrow", payment_type)

    def test_get_origin_country_and_destinations_and_payment_type_eleven(self):
        soup_html = self._get_page_as_soup_html('listings/saved_empire_listing_11')
        origin_country, destination_countries, payment_type = \
            scrapingFunctions.get_origin_country_and_destinations_and_payment_type(
                soup_html)
        self.assertEqual(origin_country, "United Kingdom")
        self.assertTupleEqual(('World Wide', 'United States', 'Asia', 'Africa', 'Antarctica(c)'), destination_countries)
        self.assertEqual("Escrow", payment_type)


class TestGetFeedbacks(EmpireBaseTest):
    def test_get_feedbacks(self):
        soup_html = self._get_page_as_soup_html("feedback/saved_empire_feedback_1")
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        a = 1
