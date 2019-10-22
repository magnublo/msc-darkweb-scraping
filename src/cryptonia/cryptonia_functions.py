from typing import List, Union

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
    def get_list_of_cateogory_list_and_url(soup_html: BeautifulSoup) -> List[Union[List[str], str]]:
        sidebar_inners = [div for div in soup_html.findAll('div', attrs={'class': 'sidebar_inner'})]
        assert len(sidebar_inners) == 2
        sidebar_inner = sidebar_inners[1]
        chksubcats_divs = [div for div in sidebar_inner.findAll('div', attrs={'class': 'chksubcats'})]
        category_name_spans = [span for span in sidebar_inner.findAll('span', attrs={'class', 'lgtext'})]
        assert len(chksubcats_divs) == len(category_name_spans) == 10

        list_of_category_list_category_url_and_nr_of_listings = []

        for chksubcats_div, category_name_span in zip(chksubcats_divs, category_name_spans):
            main_category_name = category_name_span.text.strip()
            subcategory_hrefs = [href for href in chksubcats_div.findAll('a', href=True)]
            for subcategory_href in subcategory_hrefs:
                subcategory_href_inner_text_parts = subcategory_href.text.split(" ")
                assert len(subcategory_href_inner_text_parts) == 2
                subcategory_name = subcategory_href_inner_text_parts[0].strip()
                categories = [main_category_name, subcategory_name]
                subcategory_base_url = subcategory_href["href"]
                list_of_category_list_category_url_and_nr_of_listings.append(
                    [categories, subcategory_base_url])

        return list_of_category_list_category_url_and_nr_of_listings

