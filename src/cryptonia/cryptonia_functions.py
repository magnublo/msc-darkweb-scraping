from typing import List, Tuple

from bs4 import BeautifulSoup

from definitions import CRYPTONIA_MARKET_BASE_URL
from src.base_functions import BaseFunctions


class CryptoniaScrapingFunctions(BaseFunctions):

    @staticmethod
    def accepts_currencies(soup_html) -> Tuple[bool, bool, bool]:
        pass

    @staticmethod
    def get_title(soup_html) -> str:
        pass

    @staticmethod
    def get_description(soup_html) -> str:
        pass

    @staticmethod
    def get_product_page_urls(soup_html) -> List[str]:
        product_page_urls = []

        tables = [table for table in soup_html.findAll('table', attrs={'style': 'width: 100%'})]
        assert len(tables) == 1
        table = tables[0]

        trs = [tr for tr in table.findAll('tr')]
        assert len(trs) <= 27

        for tr in trs[1:-1]:
            thumb_td, spacer_td, product_td, price_td, vendor_td = [td for td in tr.findAll('td')]
            hrefs = [href for href in product_td.findAll('a', href=True)]
            assert len(hrefs) == 1
            href = hrefs[0]
            product_page_urls.append(href["href"])

        assert len(product_page_urls) == len(trs) - 2

        return product_page_urls



    @staticmethod
    def get_nr_sold_since_date(soup_html) -> int:
        pass

    @staticmethod
    def get_fiat_currency_and_price(soup_html) -> Tuple[str, int]:
        pass

    @staticmethod
    def get_origin_country_and_destinations(soup_html) -> Tuple[str, List[str]]:
        pass

    @staticmethod
    def get_cryptocurrency_rates(soup_html: BeautifulSoup) -> Tuple[int, int]:


    def _format_logger_message(self, message: str) -> str:
        return message

    @staticmethod
    def get_category_lists_and_urls(soup_html: BeautifulSoup) -> Tuple[List[List], List[str]]:
        sidebar_inners = [div for div in soup_html.findAll('div', attrs={'class': 'sidebar_inner'})]
        assert len(sidebar_inners) == 2
        sidebar_inner = sidebar_inners[1]
        chksubcats_divs = [div for div in sidebar_inner.findAll('div', attrs={'class': 'chksubcats'})]
        category_name_spans = [span for span in sidebar_inner.findAll('span', attrs={'class', 'lgtext'})]
        assert len(chksubcats_divs) == len(category_name_spans) == 10

        category_lists = []
        urls = []

        for chksubcats_div, category_name_span in zip(chksubcats_divs, category_name_spans):
            main_category_name = category_name_span.text.strip()
            subcategory_hrefs = [href for href in chksubcats_div.findAll('a', href=True)]
            for subcategory_href in subcategory_hrefs:
                subcategory_href_inner_text_parts = subcategory_href.text.split(" ")
                assert len(subcategory_href_inner_text_parts) == 2
                subcategory_name = subcategory_href_inner_text_parts[0].strip()
                categories = [main_category_name, subcategory_name]
                subcategory_base_url = subcategory_href["href"]
                category_lists.append(categories)
                urls.append(subcategory_base_url)

        assert len(category_lists) == len(urls)
        return category_lists, urls

    @staticmethod
    def get_nr_of_result_pages_in_category(soup_html: BeautifulSoup) -> int:
        tds = [td for td in soup_html.findAll('td', attrs={'class', 'gridftr'})]
        assert len(tds) == 1
        td: BeautifulSoup = tds[0]
        spans = [span for span in td.findAll('span')]
        assert len(spans) == 2
        span: BeautifulSoup = spans[1]
        parts_of_span = span.text.split(" ")
        assert len(parts_of_span) == 3
        return int(parts_of_span[2])

    @staticmethod
    def get_titles_sellers_and_seller_urls(soup_html: BeautifulSoup) -> Tuple[List[str], List[str], List[str]]:
        titles = []
        sellers = []
        seller_urls = []

        tables = [table for table in soup_html.findAll('table', attrs={'style': 'width: 100%'})]
        assert len(tables) == 1
        table = tables[0]

        trs = [tr for tr in table.findAll('tr')]
        assert len(trs) <= 27

        for tr in trs[1:-1]:
            thumb_td, spacer_td, product_td, price_td, vendor_td = [td for td in tr.findAll('td')]
            hrefs = [href for href in vendor_td.findAll('a', href=True)]
            assert len(hrefs) == 1
            href = hrefs[0]
            seller_urls.append(f"{CRYPTONIA_MARKET_BASE_URL}{href['href']}")
            sellers.append(href.text)

            divs = [div for div in product_td.findAll('div', attrs={'style': 'margin-bottom: 5px; width: 270px; overflow: hidden'})]
            assert  len(divs) == 1
            name_div = divs[0]
            titles.append(name_div.text)

        return titles, sellers, seller_urls

