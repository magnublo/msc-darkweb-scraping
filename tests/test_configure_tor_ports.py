from time import sleep
from unittest import TestCase

from environment_settings import LOWEST_TOR_PORT
from src.configure_tor_ports import get_busy_ports
from src.tor_proxy_check import get_recommended_nr_of_tor_proxies


class TestGetBusyPorts(TestCase):

    def test_get_busy_ports(self):
        nr_of_threads = 10
        recommended_nr_of_tor_proxies = get_recommended_nr_of_tor_proxies(nr_of_threads)
        socks_port_sequence = [i for i in
                               range(LOWEST_TOR_PORT, LOWEST_TOR_PORT + recommended_nr_of_tor_proxies * 2, 2)]
        control_port_sequence = [i for i in
                                 range(LOWEST_TOR_PORT + 1, LOWEST_TOR_PORT + recommended_nr_of_tor_proxies * 2 + 1, 2)]
        busy_ports = get_busy_ports(socks_port_sequence, control_port_sequence)
        sleep(1)
