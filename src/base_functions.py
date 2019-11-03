from abc import abstractstaticmethod
from typing import Tuple

from bs4 import BeautifulSoup
from src.base_logger import BaseClassWithLogger


class BaseFunctions(BaseClassWithLogger):


    @abstractstaticmethod
    def get_captcha_image_url(soup_html: BeautifulSoup) -> str:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_meta_refresh_interval(soup_html: BeautifulSoup) -> Tuple[int, str]:
        pass

