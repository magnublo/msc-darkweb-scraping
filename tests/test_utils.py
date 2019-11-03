from unittest import TestCase

from src import utils


class TestGetLoggerName(TestCase):

    def test_get_logger_name(self):
        logger_name = utils.get_logger_name(self.__class__)
        self.assertEqual("TesGetLogNam", logger_name)
