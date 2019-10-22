from typing import List, Union, Tuple

from bs4 import BeautifulSoup

from src.base import BaseFunctions


class CryptoniaScrapingFunctions(BaseFunctions):
    def accepts_currencies(soup_html):
        pass

    def get_title(soup_html):
        pass

    def get_description(soup_html):
        pass

    def get_product_page_urls(soup_html):
        pass

    def get_nr_sold_since_date(soup_html):
        pass

    def get_fiat_currency_and_price(soup_html):
        pass

    def get_origin_country_and_destinations(soup_html):
        pass

    def get_cryptocurrency_rates(soup_html):
        pass

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
    def get_nr_of_result_pages_in_category(soup_html) -> int:
        tds = [td for td in soup_html.findAll('td', attrs={'class', 'gridftr'})]
        assert len(tds) == 1
        td: BeautifulSoup = tds[0]
        spans = [span for span in td.findAll('span')]
        assert len(spans) == 2
        span: BeautifulSoup = spans[1]
        parts_of_span = span.text.split(" ")
        assert len(parts_of_span) == 3
        return int(parts_of_span[2])

