from unittest import TestCase
import contextlib

import src.tor_proxy_check
from src import utils

class TestCheckAvailableTorProxies(TestCase):
    def test_check_available_tor_proxies(self):
        #with contextlib.redirect_stdout(None):
            src.tor_proxy_check.get_available_tor_proxies(10)
