from unittest import TestCase

from src import utils


class TestGetLoggerName(TestCase):

    def test_get_logger_name(self):
        logger_name = utils.get_logger_name(self.__class__)
        self.assertEqual("TesGetLogNam", logger_name)


class TestGetProxyPort(TestCase):
    def test_get_proxy_port(self):
        LOWEST_TOR_PORT = 9050
        TOR_PROXY_SERVER_ADDRESS = 'localhost'
        PROXIES = {
            'http': f"socks5h://{TOR_PROXY_SERVER_ADDRESS}:{LOWEST_TOR_PORT}",
            'https': f"socks5h://{TOR_PROXY_SERVER_ADDRESS}:{LOWEST_TOR_PORT}"
        }
        proxy_port = utils.get_proxy_port(PROXIES)
        self.assertEqual(9050, proxy_port)
