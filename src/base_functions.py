from abc import abstractstaticmethod
from typing import List, Tuple

from src.base_logger import BaseClassWithLogger


class BaseFunctions(BaseClassWithLogger):

    @abstractstaticmethod
    def accepts_currencies(soup_html) -> Tuple[bool, bool, bool]:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_title(soup_html) -> str:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_description(soup_html) -> str:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_product_page_urls(soup_html) -> List[str]:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_nr_sold_since_date(soup_html) -> int:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_fiat_currency_and_price(soup_html) -> Tuple[str, int]:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_origin_country_and_destinations(soup_html) -> Tuple[str, List[str]]:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_cryptocurrency_rates(soup_html) -> Tuple[int, int, int]:
        raise NotImplementedError('')
