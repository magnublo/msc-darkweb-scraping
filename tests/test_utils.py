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


class TestDetermineRealCoutry(TestCase):

    def test_determine_real_country(self):
        res = []
        names = ('France', 'India', 'Belgium', 'Brazil', 'Thailand', 'Turkey', 'Worldwide', 'Åland Islands', 'Austria',
                 'Anguilla', 'Albania', 'Aruba', 'Egypt', 'China', 'Bangladesh', 'Bolivia', 'Plurinational State of',
                 'Azerbaijan', 'United Arab Emirates')
        for name in names:
            res.append(utils.determine_real_country(name))

        b = len(names) == len(set(res))
        a = 1

    def test_determine_real_country_one(self):
        names = (
            'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'France',
            'Germany', 'Greece', 'Hungary', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands',
            'Poland',
            'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'United Kingdom', 'Ireland', 'Switzerland',
            'Liechtenstein', 'Andorra', 'Monaco', 'Finland', 'Iceland', 'Norway', 'Sweden', 'Serbia', 'San Marino',
            'Montenegro', 'Macedonia', 'the Former Yugoslav Republic of', 'Bosnia and Herzegovina', 'Albania',
            'Ukraine',
            'Moldova', 'Republic of', 'Armenia', 'Azerbaijan', 'Georgia', 'Kazakhstan', 'European Union', 'Suriname',
            'Peru')
        res = []
        names = ('France', 'India', 'Belgium', 'Brazil', 'Thailand', 'Turkey', 'Worldwide', 'Åland Islands', 'Austria',
                 'Anguilla', 'Albania', 'Aruba', 'Egypt', 'China', 'Bangladesh', 'Bolivia', 'Plurinational State of',
                 'Azerbaijan', 'United Arab Emirates')
        for name in names:
            res.append(utils.determine_real_country(name))

        b = len(names) == len(set(res))
        a = 1


class Test(TestCase):
    def test__contains_world_as_substring(self):
        # World Wide  World Wide  World Wide  World Wide  World Wi
        # World Wide  World Wide  World Wide
        continent1 = utils.determine_real_country("World Wide  World Wide  World Wide  World Wide  World Wi")
        self.assertEqual(('World', None, None, True), continent1)
        continent2 = utils.determine_real_country("World Wide  World Wide  World Wide")
        self.assertEqual(('World', None, None, True), continent2)
