from unittest import TestCase

from src.empire.empire_scrape import _get_final_quantity_in_stock


class TestGetFinalQuantityInStock(TestCase):

    def test_should_return_0(self):
        first_quantity_in_stock = 0
        second_quantity_in_stock = None

        final_quantity_in_stock = _get_final_quantity_in_stock(first_quantity_in_stock, second_quantity_in_stock)

        self.assertEqual(0, final_quantity_in_stock)

    def test_should_return_12(self):
        first_quantity_in_stock = None
        second_quantity_in_stock = 12

        final_quantity_in_stock = _get_final_quantity_in_stock(first_quantity_in_stock, second_quantity_in_stock)

        self.assertEqual(12, final_quantity_in_stock)

    def test_should_return_6(self):
        first_quantity_in_stock = 6
        second_quantity_in_stock = 12

        final_quantity_in_stock = _get_final_quantity_in_stock(first_quantity_in_stock, second_quantity_in_stock)

        self.assertEqual(6, final_quantity_in_stock)

    def test_should_return_none(self):
        first_quantity_in_stock = None
        second_quantity_in_stock = None

        final_quantity_in_stock = _get_final_quantity_in_stock(first_quantity_in_stock, second_quantity_in_stock)

        self.assertEqual(None, final_quantity_in_stock)
