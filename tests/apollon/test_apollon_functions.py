import datetime
from unittest import TestCase

from src.utils import ListingType
from tests.apollon.apollon_base_test import ApollonBaseTest
from src.apollon.apollon_functions import ApollonScrapingFunctions as scrapingFunctions


class TestApollonScrapingFunctions(ApollonBaseTest):

    def test_get_sub_category_index_urls(self):
        soup_html = self._get_page_as_soup_html('category_indexes/category_index_0')
        main_category_index_urls, parent_sub_category_index_urls = \
            [list(l) for l in scrapingFunctions.get_sub_categories_index_urls(
                soup_html)]

        parent_sub_category_index_urls.sort()
        main_category_index_urls.sort()

        self.assertListEqual(['/home.php?cid=2&csid=100', '/home.php?cid=2&csid=101', '/home.php?cid=2&csid=102',
                              '/home.php?cid=2&csid=103', '/home.php?cid=2&csid=104', '/home.php?cid=2&csid=53',
                              '/home.php?cid=2&csid=63', '/home.php?cid=2&csid=72', '/home.php?cid=2&csid=77',
                              '/home.php?cid=2&csid=81', '/home.php?cid=2&csid=85', '/home.php?cid=2&csid=94',
                              '/home.php?cid=2&csid=95', '/home.php?cid=2&csid=96'],

                             parent_sub_category_index_urls)

        self.assertListEqual(
            ['/home.php?cid=1', '/home.php?cid=10', '/home.php?cid=11', '/home.php?cid=12', '/home.php?cid=3',
             '/home.php?cid=4', '/home.php?cid=5', '/home.php?cid=8', '/home.php?cid=9'], main_category_index_urls)


class TestGetSubSubCategoryNamesUrlsAndNrsOfListings(ApollonBaseTest):
    def test_get_sub_sub_category_names_urls_and_nrs_of_listings(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        sub_sub_categories_urls_and_nrs_of_listings = scrapingFunctions.get_sub_sub_categories_urls_and_nrs_of_listings(
            soup_html)
        self.assertTupleEqual(((('Coke', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=63', 3155),
                               (('Speed', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=64', 2040),
                               (('Meth', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=65', 1203),
                               (('Crack', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=66', 113),
                               (('Adderal & Vyvanse', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=67', 526),
                               (('2-FA', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=68', 9),
                               (('Pressed Pills', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=69', 120),
                               (('Altro RCs', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=70', 133),
                               (('Other', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=71', 530)),
                              sub_sub_categories_urls_and_nrs_of_listings)


class TestGetCurrentlySelectedMainCategory(ApollonBaseTest):

    def test_get_currently_selected_main_category_zero(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        main_category_name = scrapingFunctions.get_currently_selected_main_category(soup_html)
        self.assertEquals("Drugs", main_category_name)


class TestGetCurrentlySelectedParentSubCategory(ApollonBaseTest):

    def test_get_currently_selected_parent_sub_category_zero(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        parent_sub_category_name = scrapingFunctions.get_currently_selected_parent_sub_category(soup_html)
        self.assertEquals("Stimulants", parent_sub_category_name)

    def test_get_currently_selected_parent_sub_category_two(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_2")
        parent_sub_category_name = scrapingFunctions.get_currently_selected_parent_sub_category(soup_html)
        self.assertEquals("Other", parent_sub_category_name)


class TestGetParentSubCategoryUrlsAndNrsOfListings(ApollonBaseTest):
    def test_get_parent_sub_category_urls_and_nrs_of_listings(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_1")
        parent_sub_category_urls_and_nrs_of_listings = \
            scrapingFunctions.get_parent_sub_category_urls_and_nrs_of_listings(
                soup_html)
        self.assertEquals((None, '/home.php?cid=2&csid=95', 1141), parent_sub_category_urls_and_nrs_of_listings[8])


class TestGetTaskListFromMainCategoryPage(ApollonBaseTest):
    def test_get_task_list_from_main_category_page_zero(self):
        soup_html = self._get_page_as_soup_html("category_indexes/category_index_0")
        task_list_from_main_category_page = scrapingFunctions.get_task_list_from_main_category_page(
            soup_html)
        self.assertEqual((None, '/home.php?cid=1&csid=5&ss_home=2&pg=103'), task_list_from_main_category_page[324])

    def test_get_task_list_from_main_category_page_one(self):
        soup_html = self._get_page_as_soup_html("category_indexes/category_index_1")
        task_list_from_main_category_page = scrapingFunctions.get_task_list_from_main_category_page(
            soup_html)
        self.assertEqual((None, '/home.php?cid=8&csid=29&ss_home=2&pg=1'), task_list_from_main_category_page[0])
        self.assertEqual((None, '/home.php?cid=8&csid=30&ss_home=2&pg=1'), task_list_from_main_category_page[1])


class TestGetTaskListFromParentSubCategoryPage(ApollonBaseTest):
    def test_get_task_list_from_parent_sub_category_page_zero(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        task_list_from_parent_sub_category_page = scrapingFunctions.get_task_list_from_parent_sub_category_page(
            soup_html)
        self.assertEqual((('Coke', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=63&ss_home=2&pg=210'),
                         task_list_from_parent_sub_category_page[209])
        self.assertEqual((('Speed', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=64&ss_home=2&pg=1'),
                         task_list_from_parent_sub_category_page[211])

    def test_get_task_list_from_parent_sub_category_page_one(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_1")
        task_list_from_parent_sub_category_page = scrapingFunctions.get_task_list_from_parent_sub_category_page(
            soup_html)
        self.assertEqual((('Pills', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=77&ss_home=2&pg=82'),
                         task_list_from_parent_sub_category_page[81])
        self.assertEqual((('Heroin', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=78&ss_home=2&pg=1'),
                         task_list_from_parent_sub_category_page[83])


class TestApollonGetCryptoCurrencyRates(ApollonBaseTest):

    def test_get_cryptocurrency_rates_zero(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        usd_rates = scrapingFunctions.get_cryptocurrency_rates(soup_html)
        self.assertTupleEqual((9358.88, 69.47, 386.83, 63.8), usd_rates)


class TestGetListingInfos(ApollonBaseTest):

    def test_get_listing_infos_zero(self):
        # product_page_urls, titles, urls_is_sticky, sellers, seller_urls, nrs_of_views, publication_dates, categories
        soup_html = self._get_page_as_soup_html("search_results/search_result_0")
        listing_info = scrapingFunctions.get_listing_infos(soup_html)
        self.assertTupleEqual((('/listing.php?ls_id=43473', '/listing.php?ls_id=92209', '/listing.php?ls_id=32684',
                                '/listing.php?ls_id=18920', '/listing.php?ls_id=52932', '/listing.php?ls_id=60838',
                                '/listing.php?ls_id=73431', '/listing.php?ls_id=50483', '/listing.php?ls_id=75134',
                                '/listing.php?ls_id=52904', '/listing.php?ls_id=75922', '/listing.php?ls_id=58942',
                                '/listing.php?ls_id=17205', '/listing.php?ls_id=22037', '/listing.php?ls_id=54014'), (
                                   'UK Pharma Dihydrocodeine 30mg x 42 with Free UK Shipping',
                                   "CHANGA DMT - THE SHAMANIC LION'S SOUL!", 'Jurassic Park XTC - 300mg',
                                   'MDMA - Champagne - 88%', '25x 200µg LSD Blotters',
                                   'Iranian Heroin Pure [87%]  ★ 1GR ★ [❆Intro Sale❆]',
                                   '10GR Moroccan Hash HQ | Ketama | #1 | A+++ | Free shipping',
                                   '100 x Yellow Batman 2C-B (20mg) - 10th week of January; is it pay-day yet?!?! '
                                   'SPECIAL!!!',
                                   'Zopiclone 7.5mg x 10 Sleeping Tablets Pharma',
                                   '5G Pure Needlepoint S-isomer Ketamine',
                                   'MK-677 [TOP QUALITY] - 5 GRAMS', '1 OZ TIER 1 SHATTER', '3.5g Canadian Meth',
                                   'Amnesia Haze - 23% THC',
                                   'COKE/COCAINE PURE COLUMBIAN COLO COCAINE 1G   **FREE UK DELIVERY**'), (
                                   True, True, True, True, True, True, True, True, True, True, True, True, True, True,
                                   True), (
                                   'FASTmedsUK', 'TGC-RC', 'HeinekenExpress', 'HeinekenExpress', 'Heineken',
                                   'DailyPaper',
                                   'DutchTopBoy', 'DQDinc', 'bluemagic', 'Heineken', 'TGC-RC', 'Terpzz',
                                   'PenileFractures',
                                   'HeinekenExpress', 'NARCOTICSDIRECT'), (
                                   '/user.php?u_id=FASTmedsUK', '/user.php?u_id=TGC-RC',
                                   '/user.php?u_id=HeinekenExpress',
                                   '/user.php?u_id=HeinekenExpress', '/user.php?u_id=Heineken',
                                   '/user.php?u_id=DailyPaper',
                                   '/user.php?u_id=DutchTopBoy', '/user.php?u_id=DQDinc', '/user.php?u_id=bluemagic',
                                   '/user.php?u_id=Heineken', '/user.php?u_id=TGC-RC', '/user.php?u_id=Terpzz',
                                   '/user.php?u_id=PenileFractures', '/user.php?u_id=HeinekenExpress',
                                   '/user.php?u_id=NARCOTICSDIRECT'),
                               (506, 1012, 3652, 9460, 2155, 3122, 1342, 1370, 369, 1080, 575, 2097, 1702, 2641, 4159),
                               (datetime.datetime(2019, 10, 19, 0, 0), datetime.datetime(2020, 1, 27, 0, 0),
                                datetime.datetime(2019, 8, 14, 0, 0), datetime.datetime(2019, 8, 8, 0, 0),
                                datetime.datetime(2019, 11, 26, 0, 0), datetime.datetime(2019, 12, 14, 0, 0),
                                datetime.datetime(2019, 12, 31, 0, 0), datetime.datetime(2019, 11, 28, 0, 0),
                                datetime.datetime(2019, 8, 5, 0, 0), datetime.datetime(2019, 11, 26, 0, 0),
                                datetime.datetime(2019, 12, 18, 0, 0), datetime.datetime(2019, 12, 11, 0, 0),
                                datetime.datetime(2019, 7, 28, 0, 0), datetime.datetime(2019, 8, 14, 0, 0),
                                datetime.datetime(2019, 12, 4, 0, 0)), (
                                   (('Drugs', None, None, 0), ('Opiates', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Psychedelic', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Ecstasy', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Ecstasy', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Psychedelic', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Opiates', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Psychedelic', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Prescriptions', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Disassociatives', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Steroids', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Stimulants', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                                   (('Drugs', None, None, 0), ('Stimulants', None, 'Drugs', 1)))), listing_info)

    def test_get_listing_infos_one(self):
        soup_html = self._get_page_as_soup_html("search_results/search_result_1")
        listing_info = scrapingFunctions.get_listing_infos(soup_html)
        self.assertTupleEqual((('/listing.php?ls_id=42057', '/listing.php?ls_id=45130', '/listing.php?ls_id=66123',
                                '/listing.php?ls_id=47179', '/listing.php?ls_id=87628', '/listing.php?ls_id=30284',
                                '/listing.php?ls_id=68429', '/listing.php?ls_id=70221', '/listing.php?ls_id=28237',
                                '/listing.php?ls_id=47181', '/listing.php?ls_id=47437', '/listing.php?ls_id=79694',
                                '/listing.php?ls_id=80974', '/listing.php?ls_id=86094', '/listing.php?ls_id=87118'), (
                               'Silver Haze - 20g - Weed', '10g ✿ CANNALOPE ✿ (OUTDOOR) "With Seeds"',
                               '[£27 INTRO OFFER] 3.5G GREEN CRACK CALI HIGH GRADE AAA+ UK NDD ESCROW',
                               '7g Snoop OG Medical Grade Indica', '1G WEDDING CAKE / TOP QUALITY',
                               '!SALE! 40g AUTO DAIQUIRI LIME Weed / Gras | Outdoor',
                               'LEMON HAZE >TOP<GERMAN>1G<QUALITY [FAST SHIPPING]',
                               'PROMO **** 15 Gram Super WEED *** Top Holland WEED',
                               '3.5g ** CHANNEL + ** - AAA+++ TOP SHELF', '4g Kosher Kush Medical Grade Indica',
                               '5g//TROPIMANGO', '*****$125 oz Indoor/Topshelf Flower "Pre-98 Bubba Kush"****',
                               '25gr Purple Haze B-grade (Outdoor & Organic & Fermented/Cured)',
                               '7G | GRINDED BUD - BATCH NO.2 | FREE POST', 'Green Gelato Flower Greenhouse 8oz'), (
                               False, False, False, False, False, False, False, False, False, False, False, False, False, False,
                               False), ('DrSommer', 'MARLEYS-SHOP', 'mad_max', 'green_usa', 'kwayuk', 'Hobby_Gaertner',
                                       'German-Quality', 'AndyMacht', 'GreenConnection', 'green_usa', 'thegreenrobots',
                                       'TrueVape', 'GoldenCamel', 'BookFace', 'Seedless'), (
                               '/user.php?u_id=DrSommer', '/user.php?u_id=MARLEYS-SHOP', '/user.php?u_id=mad_max',
                               '/user.php?u_id=green_usa', '/user.php?u_id=kwayuk', '/user.php?u_id=Hobby_Gaertner',
                               '/user.php?u_id=German-Quality', '/user.php?u_id=AndyMacht',
                               '/user.php?u_id=GreenConnection', '/user.php?u_id=green_usa',
                               '/user.php?u_id=thegreenrobots', '/user.php?u_id=TrueVape', '/user.php?u_id=GoldenCamel',
                               '/user.php?u_id=BookFace', '/user.php?u_id=Seedless'),
                               (372, 173, 186, 230, 40, 343, 128, 131, 716, 230, 160, 107, 148, 30, 85), (
                               datetime.datetime(2019, 11, 12, 0, 0), datetime.datetime(2019, 11, 21, 0, 0),
                               datetime.datetime(2019, 12, 19, 0, 0), datetime.datetime(2019, 11, 24, 0, 0),
                               datetime.datetime(2020, 1, 19, 0, 0), datetime.datetime(2019, 10, 4, 0, 0),
                               datetime.datetime(2019, 12, 22, 0, 0), datetime.datetime(2019, 12, 25, 0, 0),
                               datetime.datetime(2019, 6, 22, 0, 0), datetime.datetime(2019, 11, 24, 0, 0),
                               datetime.datetime(2019, 11, 24, 0, 0), datetime.datetime(2020, 1, 7, 0, 0),
                               datetime.datetime(2020, 1, 9, 0, 0), datetime.datetime(2019, 11, 26, 0, 0),
                               datetime.datetime(2019, 11, 22, 0, 0)), (
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)),
                               (('Drugs', None, None, 0), ('Cannabis & Hashish', None, 'Drugs', 1)))), listing_info)


class TestGetSubSubCategoriesUrlsAndNrsOfListings(ApollonBaseTest):

    def test_get_sub_sub_categories_urls_and_nrs_of_listings_zero(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        sub_sub_categories_urls_and_nrs_of_listings = scrapingFunctions.get_sub_sub_categories_urls_and_nrs_of_listings(
            soup_html)
        self.assertTupleEqual(((('Coke', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=63', 3155),
                               (('Speed', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=64', 2040),
                               (('Meth', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=65', 1203),
                               (('Crack', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=66', 113),
                               (('Adderal & Vyvanse', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=67', 526),
                               (('2-FA', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=68', 9),
                               (('Pressed Pills', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=69', 120),
                               (('Altro RCs', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=70', 133),
                               (('Other', None, 'Stimulants', 2), '/home.php?cid=2&csid=63&ssid=71', 530)),
                              sub_sub_categories_urls_and_nrs_of_listings)

    def test_get_sub_sub_categories_urls_and_nrs_of_listings_one(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_1")
        sub_sub_categories_urls_and_nrs_of_listings = scrapingFunctions.get_sub_sub_categories_urls_and_nrs_of_listings(
            soup_html)
        self.assertTupleEqual(((('Pills', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=77', 1239),
                               (('Heroin', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=78', 1094),
                               (('RCs', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=79', 122),
                               (('Other', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=80', 303),
                               (('Opiates Substitutes', None, 'Opiates', 2), '/home.php?cid=2&csid=77&ssid=105', 134)),
                              sub_sub_categories_urls_and_nrs_of_listings)


class TestAcceptsCurrencies(ApollonBaseTest):
    def test_accepts_currencies_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        XMR, BCH, LTC = scrapingFunctions.accepts_currencies(soup_html)
        self.assertTupleEqual((True, True, True), (XMR, BCH, LTC))


class TestGetSales(ApollonBaseTest):
    def test_get_sales_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        sales = scrapingFunctions.get_sales(soup_html)
        self.assertEqual(17, sales)


class TestGetFiatPrice(ApollonBaseTest):
    def test_get_fiat_price_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        fiat_price = scrapingFunctions.get_fiat_price(soup_html)
        self.assertEqual(4.00, fiat_price)


class TestGetDestinationCountries(ApollonBaseTest):

    def test_get_destination_countries_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        destination_countries = scrapingFunctions.get_destination_countries(soup_html)
        self.assertTupleEqual(('United States',), destination_countries)

    def test_get_destination_countries_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        destination_countries = scrapingFunctions.get_destination_countries(soup_html)
        self.assertTupleEqual(('World Wide', 'Europe', 'Netherlands', 'United Kingdom', 'Germany'),
                              destination_countries)


class TestGetPaymentMethod(ApollonBaseTest):

    def test_get_payment_method_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        escrow, fifty_percent_finalize_early = scrapingFunctions.get_payment_method(soup_html)
        self.assertTupleEqual((True, False), (escrow, fifty_percent_finalize_early))

    def test_get_payment_method_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        escrow, fifty_percent_finalize_early = scrapingFunctions.get_payment_method(soup_html)
        self.assertTupleEqual((True, False), (escrow, fifty_percent_finalize_early))


class TestGetStandardizedListingType(ApollonBaseTest):

    def test_get_standardized_listing_type_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        listing_type = scrapingFunctions.get_standardized_listing_type(soup_html)
        self.assertEqual(ListingType.PHYSICAL, listing_type)

    def test_get_standardized_listing_type_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        listing_type = scrapingFunctions.get_standardized_listing_type(soup_html)
        self.assertEqual(ListingType.PHYSICAL, listing_type)


class TestGetQuantityInStock(ApollonBaseTest):

    def test_get_quantity_in_stock_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        quantity_in_stock = scrapingFunctions.get_quantity_in_stock(soup_html)
        self.assertEqual(None, quantity_in_stock)

    def test_get_quantity_in_stock_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        quantity_in_stock = scrapingFunctions.get_quantity_in_stock(soup_html)
        self.assertEqual(None, quantity_in_stock)

    def test_get_quantity_in_stock_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2")
        quantity_in_stock = scrapingFunctions.get_quantity_in_stock(soup_html)
        self.assertEqual(97, quantity_in_stock)


class TestGetShippingMethods(ApollonBaseTest):

    def test_get_shipping_methods_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_0")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('free USPS letter UNTRACKED no reships or refunds', 9, 'USD', 0.0, None, False),
                               ('USPS Priority TRACKED', 10, 'USD', 11.0, None, False),
                               ('USPS Package TRACKED', 14, 'USD', 5.0, None, False)),
                              shipping_methods)

    def test_get_shipping_methods_one(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual((('Default', 1, 'USD', 0.0, None, False),), shipping_methods)

    def test_get_shipping_methods_two(self):
        soup_html = self._get_page_as_soup_html("listings/listing_2")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual(
            (('UK Free Shipping', 3, 'USD', 0.0, None, False), ('EU Shipping', 10, 'USD', 5.27, None, False)),
            shipping_methods)

    def test_get_shipping_methods_three(self):
        soup_html = self._get_page_as_soup_html("listings/listing_3")
        shipping_methods = scrapingFunctions.get_shipping_methods(soup_html)
        self.assertTupleEqual(
            (('UK Free Shipping', 3, 'USD', 0.0, None, False), ('EU Shipping', 10, 'USD', 5.27, None, False)),
            shipping_methods)

class TestGetListingText(ApollonBaseTest):

    def test_get_listing_text_zero(self):
        soup_html = self._get_page_as_soup_html("listings/listing_1")
        listing_text = scrapingFunctions.get_listing_text(soup_html)
        self.assertTrue(len(listing_text) > 10)


class TestGetEmailAndJabberId(ApollonBaseTest):

    def test_get_email_and_jabber_id_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        email, jabber_id = scrapingFunctions.get_email_and_jabber_id(soup_html)
        self.assertEqual(("joris127@torbox3uiot6wchz.onion", None), (email, jabber_id))

    def test_get_email_and_jabber_id_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        email, jabber_id = scrapingFunctions.get_email_and_jabber_id(soup_html)
        self.assertEqual(("raca@fakemail.com", None), (email, jabber_id))

    def test_get_email_and_jabber_id_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2")
        email, jabber_id = scrapingFunctions.get_email_and_jabber_id(soup_html)
        self.assertEqual((None, 'diego-hundreds@xmpp.jp'), (email, jabber_id))


class TestGetSellerAndTrustLevel(ApollonBaseTest):

    def test_get_seller_and_trust_level_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        seller_level, trust_level = scrapingFunctions.get_seller_and_trust_level(soup_html)
        self.assertEqual(1, seller_level)
        self.assertEqual(3, trust_level)

    def test_get_seller_and_trust_level_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        seller_level, trust_level = scrapingFunctions.get_seller_and_trust_level(soup_html)
        self.assertEqual(3, seller_level)
        self.assertEqual(5, trust_level)

    def test_get_seller_and_trust_level_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3")
        seller_level, trust_level = scrapingFunctions.get_seller_and_trust_level(soup_html)
        self.assertEqual(0, seller_level)
        self.assertEqual(0, trust_level)


class TestGetPositiveFeedbackPercent(ApollonBaseTest):

    def test_get_positive_feedback_percent_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        positive_feedback_percent = scrapingFunctions.get_positive_feedback_percent(soup_html)
        self.assertEqual(100, positive_feedback_percent)

    def test_get_positive_feedback_percent_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        positive_feedback_percent = scrapingFunctions.get_positive_feedback_percent(soup_html)
        self.assertEqual(100, positive_feedback_percent)

    def test_get_positive_feedback_percent_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2")
        positive_feedback_percent = scrapingFunctions.get_positive_feedback_percent(soup_html)
        self.assertEqual(99, positive_feedback_percent)

    def test_get_positive_feedback_percent_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3")
        positive_feedback_percent = scrapingFunctions.get_positive_feedback_percent(soup_html)
        self.assertEqual(100, positive_feedback_percent)


class TestGetRegistrationDate(ApollonBaseTest):

    def test_get_registration_date_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        registration_date = scrapingFunctions.get_registration_date(soup_html)
        self.assertEqual("2019-12-05 00:00:00", str(registration_date))

    def test_get_registration_date_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        registration_date = scrapingFunctions.get_registration_date(soup_html)
        self.assertEqual("2019-09-30 00:00:00", str(registration_date))


class TestGetLastLogin(ApollonBaseTest):

    def test_get_last_login_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        last_login = scrapingFunctions.get_last_login(soup_html)
        self.assertEqual("2020-02-03 00:00:00", str(last_login))

    def test_get_last_login_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        last_login = scrapingFunctions.get_last_login(soup_html)
        self.assertEqual("2020-02-03 00:00:00", str(last_login))


class TestGetSalesBySeller(ApollonBaseTest):

    def test_get_sales_by_seller_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        sales = scrapingFunctions.get_sales_by_seller(soup_html)
        self.assertEqual(93, sales)

    def test_get_sales_by_seller_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2")
        sales = scrapingFunctions.get_sales_by_seller(soup_html)
        self.assertEqual(216, sales)


class TestGetOrders(ApollonBaseTest):

    def test_get_orders_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        orders = scrapingFunctions.get_orders(soup_html)
        self.assertEqual(0, orders)

    def test_get_orders_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        orders = scrapingFunctions.get_orders(soup_html)
        self.assertEqual(0, orders)

    def test_get_orders_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2")
        orders = scrapingFunctions.get_orders(soup_html)
        self.assertEqual(0, orders)


class TestGetDisputes(ApollonBaseTest):
    def test_get_disputes_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        disputes_won, disputes_lost = scrapingFunctions.get_disputes(soup_html)
        self.assertTupleEqual((0, 0), (disputes_won, disputes_lost))

    def test_get_disputes_four(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_4")
        disputes_won, disputes_lost = scrapingFunctions.get_disputes(soup_html)
        self.assertTupleEqual((2, 0), (disputes_won, disputes_lost))


class TestGetFeAllowed(ApollonBaseTest):

    def test_get_fe_allowed_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        fe_is_allowed = scrapingFunctions.get_fe_allowed(soup_html)
        self.assertEqual(fe_is_allowed, False)

    def test_get_fe_allowed_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        fe_is_allowed = scrapingFunctions.get_fe_allowed(soup_html)
        self.assertEqual(fe_is_allowed, True)


class TestGetMostRecentFeedback(ApollonBaseTest):
    def test_get_most_recent_feedback_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        latest_feedback_text = scrapingFunctions.get_most_recent_feedback(soup_html)
        self.assertEqual(
            'It\'s a really fast shipping and really good stuff! I will come back defenatly and thank for really '
            'secure shippment!!!',
            latest_feedback_text)

    def test_get_most_recent_feedback_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3")
        latest_feedback_text = scrapingFunctions.get_most_recent_feedback(soup_html)
        self.assertEqual(None, latest_feedback_text)


class TestGetExternalMarketRatings(ApollonBaseTest):

    def test_get_external_market_ratings_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_market_ratings)

    def test_get_external_market_ratings_one(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_1")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((('DREAM_MARKET', 1400, 4.96, None, None, None, None, None),
                               ('EMPIRE_MARKET', 410, None, None, 350, 4, 0, None),
                               ('BERLUSCONI_MARKET', 1685, None, None, 1094, 10, 7, None)), external_market_ratings)

    def test_get_external_market_ratings_two(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_2")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertEqual((('DREAM_MARKET', 1450, 4.95, None, None, None, None, None),
                          ('EMPIRE_MARKET', 1040, None, None, 706, 17, 10, None),
                          ('NIGHTMARE_MARKET', 547, None, None, 334, 0, 3, None),
                          ('CRYPTONIA_MARKET', 47, 91.0, None, None, None, None, None)), external_market_ratings)

    def test_get_external_market_ratings_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_market_ratings)

    def test_get_external_market_ratings_four(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_4")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((('DREAM_MARKET', 8400, 4.88, None, None, None, None, None),
                               ('EMPIRE_MARKET', 7694, None, None, 5778, 200, 113, None)), external_market_ratings)

    def test_get_external_market_ratings_five(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_5")
        external_market_ratings = scrapingFunctions.get_external_market_ratings(soup_html)
        self.assertTupleEqual((), external_market_ratings)


class TestGetFeedbackCategoriesAndUrls(ApollonBaseTest):
    def test_get_feedback_categories_and_urls_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        categories, urls = scrapingFunctions.get_feedback_categories_and_urls(soup_html)
        self.assertTupleEqual(('Positive', 'Neutral', 'Negative'), categories)
        self.assertTupleEqual(('/user.php?u_id=dutch-skills&tab=2', '/user.php?u_id=dutch-skills&tab=3',
                               '/user.php?u_id=dutch-skills&tab=4'), urls)

    def test_get_feedback_categories_and_urls_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3")
        categories, urls = scrapingFunctions.get_feedback_categories_and_urls(soup_html)
        self.assertTupleEqual(('Positive', 'Neutral', 'Negative'), categories)
        self.assertTupleEqual(('/user.php?u_id=usingPython1&tab=2', '/user.php?u_id=usingPython1&tab=3',
                               '/user.php?u_id=usingPython1&tab=4'), urls)


class TestGetPgpUrl(ApollonBaseTest):
    def test_get_pgp_url_zero(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_0")
        pgp_url = scrapingFunctions.get_pgp_url(soup_html)
        self.assertEqual('/user.php?u_id=dutch-skills&tab=6', pgp_url)

    def test_get_pgp_url_three(self):
        soup_html = self._get_page_as_soup_html("sellers/seller_3")
        pgp_url = scrapingFunctions.get_pgp_url(soup_html)
        self.assertEqual('/user.php?u_id=usingPython1&tab=6', pgp_url)


class TestApollonGetFeedbacks(ApollonBaseTest):
    def test_get_feedbacks_zero(self):
        soup_html = self._get_page_as_soup_html("feedbacks/positive_feedback_0")
        feedbacks = scrapingFunctions.get_feedbacks(soup_html)
        self.assertTupleEqual(((datetime.datetime(2020, 2, 3, 2, 59), 'Diffidence',
                                '10.10 for price and quality will be back for more', 'd35dba05', 'D...e', 'USD',
                                '850.00', '/listing.php?ls_id=90422'), (datetime.datetime(2020, 2, 2, 3, 49),
                                                                        'INTRO 7G BOLIVIAN 72�% £250 Check our new '
                                                                        'brick stock 10/10',
                                                                        'No Comment', '3099c443', 'y...e', 'USD',
                                                                        '252.00', '/listing.php?ls_id=23290'), (
                                   datetime.datetime(2020, 1, 31, 5, 19),
                                   'Powerful sociable Cocaine intro sale! 60% - 1G £30', '5*', '3c26f6ea', 'a...d',
                                   'USD',
                                   '33.00', '/listing.php?ls_id=29703'), (datetime.datetime(2020, 1, 31, 5, 19),
                                                                          'Powerful sociable Cocaine intro sale! 60% '
                                                                          '- 1G '
                                                                          '£30',
                                                                          '5*', '3c26f6ea', 'a...d', 'USD', '33.00',
                                                                          '/listing.php?ls_id=29703'), (
                                   datetime.datetime(2020, 1, 31, 3, 4), 'Intro Top Colombian 93% Cocaine 10g',
                                   "Had similar problems to others over xmas with this guy, but he's sound and will "
                                   "get "
                                   "it sorted.  Great CS, ok stealth, not tried the product yet, but it's fat, "
                                   "well overweight to make up for the wait.  Will def use again, just hope I can find "
                                   "him if this s",
                                   '86229c36', 'm...s', 'USD', '502.00', '/listing.php?ls_id=23295'), (
                                   datetime.datetime(2020, 1, 31, 12, 7),
                                   'Powerful sociable Cocaine intro sale! 60% - 3.5G £100', '3.7g, perfect as always',
                                   '03a83169', 'b...8', 'USD', '103.00', '/listing.php?ls_id=29704'), (
                                   datetime.datetime(2020, 1, 30, 11, 54),
                                   'Powerful sociable Cocaine intro sale! 60% - 1G £30', 'No Comment', '3099c443',
                                   's...t',
                                   'USD', '33.00', '/listing.php?ls_id=29703'), (
                                   datetime.datetime(2020, 1, 30, 10, 24), 'NEW FIRE BATCH Top Columbian Cocaine 1G',
                                   'OPretty good, fast delivery', 'bd9158e5', 'w...t', 'USD', '62.00',
                                   '/listing.php?ls_id=23681'), (datetime.datetime(2020, 1, 30, 5, 36),
                                                                 'INTRO 7G BOLIVIAN 72�% £250 Check our new brick '
                                                                 'stock '
                                                                 '10/10',
                                                                 'No Comment', '3099c443', 'y...e', 'USD', '265.00',
                                                                 '/listing.php?ls_id=23290'), (
                                   datetime.datetime(2020, 1, 29, 3, 28),
                                   'Powerful sociable Cocaine intro sale! 60% - 3.5G £100',
                                   'cheers buddy, nice and quick.',
                                   '61a10a8b', 's...y', 'USD', '110.00', '/listing.php?ls_id=29704'), (
                                   datetime.datetime(2020, 1, 29, 2, 12), 'Intro Top Colombian 93% Cocaine 0.5g',
                                   'top team', 'afc10835', 'B...1', 'USD', '32.00', '/listing.php?ls_id=23260'), (
                                   datetime.datetime(2020, 1, 29, 3, 17), 'Intro Top Colombian 93% Cocaine 0.25g',
                                   'Great. thanks!', 'e71066e7', 'c...r', 'USD', '17.00', '/listing.php?ls_id=23258'), (
                                   datetime.datetime(2020, 1, 29, 2, 10), 'Intro Top Colombian 93% Cocaine 14g',
                                   'BRILIANT VENDOR BEST ON HERE OVERWEIGHT PRIE GREAT PRODUCT AMAZING', 'b2716b1a',
                                   'm...5', 'USD', '608.00', '/listing.php?ls_id=23304'), (
                                   datetime.datetime(2020, 1, 28, 10, 8), 'Intro Top Colombian 93% Cocaine 7g',
                                   'Came 1g+ overweight to make up for xmas mixup - lovely gear NDD - UKNK pluggy.',
                                   '39df41f5', 'J...1', 'USD', '302.00', '/listing.php?ls_id=23288'), (
                                   datetime.datetime(2020, 1, 28, 9, 52),
                                   'Powerful sociable Cocaine intro sale! 60% - 1G £30', '4DD to UK', 'e3e2da4e',
                                   'p...5',
                                   'USD', '33.00', '/listing.php?ls_id=29703')), feedbacks)


class TestGetNextFeedbackUrl(ApollonBaseTest):

    def test_get_next_feedback_url_zero(self):
        soup_html = self._get_page_as_soup_html("feedbacks/positive_feedback_0")
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual('/user.php?u_id=UKNEXTDAY&tab=2&pg=2', next_feedback_url)

    def test_get_next_feedback_url_three(self):
        soup_html = self._get_page_as_soup_html("feedbacks/positive_feedback_3")
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual(None, next_feedback_url)

    def test_get_next_feedback_url_zero_3(self):
        soup_html = self._get_page_as_soup_html("feedbacks/negative_feedback_0")
        next_feedback_url = scrapingFunctions.get_next_feedback_url(soup_html)
        self.assertEqual(None, next_feedback_url)
