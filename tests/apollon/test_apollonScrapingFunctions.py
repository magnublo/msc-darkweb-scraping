from unittest import TestCase

from tests.apollon.apollon_base_test import ApollonBaseTest
from src.apollon.apollon_functions import ApollonScrapingFunctions as scrapingFunctions


class TestApollonScrapingFunctions(ApollonBaseTest):

    def test_get_sub_category_index_urls(self):
        soup_html = self._get_page_as_soup_html('category_indexes/category_index_0')
        parent_sub_category_index_urls, childless_sub_category_index_urls = \
            [list(l) for l in scrapingFunctions.get_sub_categories_index_urls(
                soup_html)]

        parent_sub_category_index_urls.sort()
        childless_sub_category_index_urls.sort()

        self.assertListEqual(['home.php?cid=1&csid=1', 'home.php?cid=1&csid=2', 'home.php?cid=1&csid=3',
                              'home.php?cid=1&csid=4', 'home.php?cid=1&csid=5', 'home.php?cid=10&csid=38',
                              'home.php?cid=10&csid=39', 'home.php?cid=10&csid=40', 'home.php?cid=10&csid=41',
                              'home.php?cid=10&csid=42', 'home.php?cid=11&csid=43', 'home.php?cid=11&csid=44',
                              'home.php?cid=11&csid=45', 'home.php?cid=11&csid=46', 'home.php?cid=11&csid=47',
                              'home.php?cid=11&csid=48', 'home.php?cid=12&csid=49', 'home.php?cid=2&csid=100',
                              'home.php?cid=2&csid=101', 'home.php?cid=2&csid=102', 'home.php?cid=2&csid=103',
                              'home.php?cid=2&csid=104', 'home.php?cid=2&csid=94', 'home.php?cid=2&csid=95',
                              'home.php?cid=3&csid=10', 'home.php?cid=3&csid=11', 'home.php?cid=3&csid=12',
                              'home.php?cid=3&csid=13', 'home.php?cid=4&csid=14', 'home.php?cid=4&csid=16',
                              'home.php?cid=4&csid=17', 'home.php?cid=5&csid=18', 'home.php?cid=5&csid=19',
                              'home.php?cid=5&csid=20', 'home.php?cid=5&csid=21', 'home.php?cid=8&csid=29',
                              'home.php?cid=8&csid=30', 'home.php?cid=8&csid=31', 'home.php?cid=8&csid=32',
                              'home.php?cid=9&csid=33', 'home.php?cid=9&csid=34', 'home.php?cid=9&csid=35',
                              'home.php?cid=9&csid=36', 'home.php?cid=9&csid=37'],

                             childless_sub_category_index_urls)

        self.assertListEqual(['home.php?cid=2&csid=53', 'home.php?cid=2&csid=63', 'home.php?cid=2&csid=72',
                              'home.php?cid=2&csid=77', 'home.php?cid=2&csid=81', 'home.php?cid=2&csid=85',
                              'home.php?cid=2&csid=96'], parent_sub_category_index_urls)


class TestGetSubSubCategoryNamesUrlsAndNrsOfListings(ApollonBaseTest):
    def test_get_sub_sub_category_names_urls_and_nrs_of_listings(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        sub_sub_categories_urls_and_nrs_of_listings = scrapingFunctions.get_sub_sub_categories_urls_and_nrs_of_listings(
            soup_html)
        self.assertTupleEqual(((('Coke', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=63', 3155),
                               (('Speed', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=64', 2040),
                               (('Meth', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=65', 1203),
                               (('Crack', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=66', 113),
                               (('Adderal & Vyvanse', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=67', 526),
                               (('2-FA', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=68', 9),
                               (('Pressed Pills', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=69', 120),
                               (('Altro RCs', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=70', 133),
                               (('Other', None, 'Stimulants', 2), 'home.php?cid=2&csid=63&ssid=71', 530)),
                              sub_sub_categories_urls_and_nrs_of_listings)


class TestGetCurrentlySelectedMainCategory(ApollonBaseTest):

    def test_get_currently_selected_main_category_zero(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        main_category_name = scrapingFunctions.get_currently_selected_main_category(soup_html)
        self.assertEquals("Drugs", main_category_name)


class TestGetCurrentlySelectedParentSubCategory(ApollonBaseTest):

    def test_get_currently_selected_parent_sub_category(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        parent_sub_category_name = scrapingFunctions.get_currently_selected_parent_sub_category(soup_html)
        self.assertEquals("Stimulants", parent_sub_category_name)


class TestGetMainCategoryUrlsAndNrsOfListings(ApollonBaseTest):
    def test_get_main_category_urls_and_nrs_of_listings(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        main_category_urls_and_nrs_of_listings = scrapingFunctions.get_parent_sub_category_urls_and_nrs_of_listings(
            soup_html)
        self.assertEquals("Stimulants", main_category_urls_and_nrs_of_listings)


class TestGetTaskListFromMainCategoryPage(ApollonBaseTest):
    def test_get_task_list_from_main_category_page(self):
        soup_html = self._get_page_as_soup_html("category_indexes/category_index_0")
        task_list_from_main_category_page = scrapingFunctions.get_task_list_from_main_category_page(
            soup_html)
        a = 0


class TestGetTaskListFromParentSubCategoryPage(ApollonBaseTest):
    def test_get_task_list_from_parent_sub_category_page(self):
        soup_html = self._get_page_as_soup_html("sub_category_indexes/sub_category_index_0")
        task_list_from_main_category_page = scrapingFunctions.get_task_list_from_parent_sub_category_page(
            soup_html)
        a = 0
