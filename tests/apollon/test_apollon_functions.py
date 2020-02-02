import datetime
from unittest import TestCase

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
        parent_sub_category_urls_and_nrs_of_listings = scrapingFunctions.get_parent_sub_category_urls_and_nrs_of_listings(
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
                                   '100 x Yellow Batman 2C-B (20mg) - 10th week of January; is it pay-day yet?!?! SPECIAL!!!',
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
