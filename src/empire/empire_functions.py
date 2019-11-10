import re
from datetime import datetime
from typing import List, Tuple, Optional
from urllib.parse import urlparse

import dateparser as dateparser
from bs4 import BeautifulSoup

from src.base.base_functions import BaseFunctions
from definitions import EMPIRE_MARKET_EXTERNAL_MARKET_STRINGS, CURRENCY_COLUMN_LENGTH, ONE_DAY
from src.db_utils import shorten_and_sanitize_for_text_column
from src.utils import parse_int, parse_time_delta_from_string, parse_float

ASSUMED_MAXIMUM_LISTINGS_PER_SEARCH_RESULT = 15
ONION_URl_REGEX = re.compile(r"^https?\:\/\/[\w\-\.]+\.onion")


def _parse_external_market_rating(titled_span: BeautifulSoup, remaining_external_market_ratings: List[str]) -> Optional[
    Tuple[
        str, int, float, List[str]]]:
    for market_id, market_string in remaining_external_market_ratings:
        if titled_span["title"].find(market_string) != -1:
            parts = titled_span.text.split(" ")
            sales = int(parts[1])
            rating = float(parts[2][1:-1])
            remaining_external_market_ratings.remove((market_id, market_string))
            return market_id, sales, rating, remaining_external_market_ratings

    return None


class EmpireScrapingFunctions(BaseFunctions):

    @staticmethod
    def accepts_currencies(soup_html):
        soup_html_as_string = str(soup_html)

        accepts_BTC = soup_html_as_string.find('btc_small.png') >= 0
        accepts_LTC = soup_html_as_string.find('ltc_small.png') >= 0
        accepts_XMR = soup_html_as_string.find('xmr_small.png') >= 0
        return accepts_BTC, accepts_LTC, accepts_XMR

    @staticmethod
    def get_title(soup_html):
        a_tags = soup_html.findAll('title')
        assert len(a_tags) == 1
        return a_tags[0].text

    @staticmethod
    def get_description(soup_html):
        descriptions = [div for div in soup_html.findAll('div', attrs={'class': 'tabcontent'})]
        assert len(descriptions) == 1
        description = descriptions[0].text
        return shorten_and_sanitize_for_text_column(description)

    @staticmethod
    def get_product_page_urls(soup_html: BeautifulSoup) -> Tuple[Tuple[str], Tuple[bool]]:
        centre_columns = [div for div in soup_html.findAll('div', attrs={'class': 'col-1centre'})]
        product_page_urls: List[str] = []
        urls_is_sticky: List[bool] = []

        for column in centre_columns:
            is_sticky = False
            divs_with_head_name = [div for div in column.findAll('div', attrs={'class': 'head'})]
            assert len(divs_with_head_name) == 1
            hrefs = [href for href in divs_with_head_name[0].findAll('a', href=True)]
            assert len(hrefs) == 2
            b_tags = [b_tag for b_tag in divs_with_head_name[0].findAll('b')]
            for b_tag in b_tags:
                if b_tag.text == "[sticky]":
                    is_sticky = True

            urls_is_sticky.append(is_sticky)
            product_page_urls.append(urlparse(hrefs[0]['href']).path)

        assert len(product_page_urls) <= ASSUMED_MAXIMUM_LISTINGS_PER_SEARCH_RESULT

        assert len(urls_is_sticky) == len(product_page_urls)

        return tuple(product_page_urls), tuple(urls_is_sticky)

    @staticmethod
    def get_nr_sold_since_date(soup_html):
        list_descriptions = [div for div in soup_html.findAll('div', attrs={'class': 'listDes'})]
        assert len(list_descriptions) == 1
        list_description = list_descriptions[0]

        spans = [span for span in list_description.findAll('span')]
        span = spans[0]
        nr_sold, date = span.text.split(" sold since ")

        date = dateparser.parse(date)

        return nr_sold, date

    @staticmethod
    def get_fiat_currency_and_price(soup_html):
        padps = [div for div in soup_html.findAll('p', attrs={'class': 'padp'})]
        assert len(padps) == 4
        text = padps[3].text
        pattern = "Purchase price: "
        pattern_index = text.find(pattern)
        text = text[pattern_index + len(pattern):]
        currency, price = text.split(" ")
        price = price.replace(",", "")
        return currency, price

    @staticmethod
    def get_origin_country_and_destinations_and_payment_type(soup_html) -> Tuple[str, Tuple[str], str]:
        tables = [table for table in soup_html.findAll('table', attrs={'class': 'productTbl'})]
        table = tables[0]
        tbodies = [tbody for tbody in table.findAll('tbody')]
        assert len(tbodies) == 1
        tbody = tbodies[0]
        trs = [tr for tr in tbody.findAll('tr')]
        assert len(trs) == 3
        tr = trs[0]
        tds = [td for td in tr.findAll('td')]
        assert len(tds) == 4
        td = tds[3]
        origin_country = td.text.strip()

        tr = trs[1]
        tds = [td for td in tr.findAll('td')]
        assert len(tds) == 4
        td = tds[3]
        destination_countries: List[str] = [td.text[a.regs[0][0]:a.regs[0][1]].strip() for a in
                                            BaseFunctions.COMMA_SEPARATED_COUNTRY_REGEX.finditer(td.text)]

        tr = trs[2]
        tds = [td for td in tr.findAll('td')]
        assert len(tds) == 4
        td = tds[3]
        payment_type = td.text.strip()

        return origin_country, tuple(destination_countries), payment_type

    @staticmethod
    def get_cryptocurrency_rates(soup_html):
        divs = [div for div in soup_html.findAll('div', attrs={'class': 'statistics'})]
        assert len(divs) == 4
        currency_rates = []
        for div in divs[:-1]:
            ps = [p for p in div.findAll('p', attrs={'class': 'padp'})]
            assert len(ps) == 6
            currency_rates.append(ps[0].findAll('font')[0].text.strip())

        assert len(currency_rates) == 3
        return currency_rates

    @staticmethod
    def get_parenthesis_number_and_vendor_and_trust_level(soup_html):
        user_info_mid_heads = [h3 for h3 in soup_html.findAll('h3', attrs={'class': 'user_info_mid_head'})]
        assert len(user_info_mid_heads) == 1
        user_info_mid_head = user_info_mid_heads[0]

        first_span = [span for span in user_info_mid_head.findAll('span')][0]

        if first_span.text.find("(") != -1:
            parenthesis_number = first_span.text[1:-1]
        else:
            parenthesis_number = None

        spans = []
        vendor_level = None
        trust_level = None

        for i in range(0, 20):
            className = "user_info_trust level-" + str(i)
            spans = spans + [span for span in user_info_mid_head.findAll('span', attrs={'class': className})]
            if len(spans) > 0:
                for span in spans:
                    if span.text.find("Vendor") >= 0:
                        vendor_level = span.text.split(" ")[2]
                    if span.text.find("Trust") >= 0:
                        trust_level = span.text.split(" ")[2]
                    if vendor_level is not None and trust_level is not None:
                        return parenthesis_number, vendor_level, trust_level

        assert False

    @staticmethod
    def get_listing_categories(soup_html: BeautifulSoup, mirror_base_url: str) -> Tuple[
        Tuple[str, int, Optional[str], Optional[int]]]:
        # each element has name, marketside_id, parent_name and level

        listing_categories: List[Tuple[str, int, Optional[str], Optional[int]]] = []

        h3s = [div for div in soup_html.findAll('h3')]
        for h3 in h3s:
            a_tags = [a_tag for a_tag in h3.findAll('a', href=True)]
            if len(a_tags) == 1:
                if a_tags[0]["href"].find(f"{mirror_base_url}/category/") != -1:
                    category = a_tags[0].text.strip()
                    url = str(a_tags[0]['href'])
                    url_fragments = url.split("/")
                    marketside_category_id = int(url_fragments[-2])
                    parent_category_name = listing_categories[-1][0] if len(listing_categories) > 0 else None
                    listing_categories.append(
                        (category, marketside_category_id, parent_category_name, len(listing_categories)))
                    # TODO: Ignoring parent name and level for now

        return tuple(listing_categories)

    @staticmethod
    def get_titles_and_sellers(soup_html: BeautifulSoup) -> Tuple[Tuple[str], Tuple[str], Tuple[str]]:
        titles: List[str] = []
        sellers: List[str] = []
        seller_urls: List[str] = []

        col_1centres = [div for div in soup_html.findAll('div', attrs={'class': 'col-1centre'})]
        assert len(col_1centres) <= ASSUMED_MAXIMUM_LISTINGS_PER_SEARCH_RESULT
        assert len(col_1centres) > 0
        for col1_centre in col_1centres:
            head_tags = [div for div in col1_centre.findAll('div', attrs={'class': 'head'})]
            assert len(head_tags) == 1
            href_links = [href for href in head_tags[0].findAll('a', href=True)]
            titles.append(href_links[0].text)
            padp_p_tags = [p for p in head_tags[0].findAll('p', attrs={'class': 'padp'})]
            assert len(padp_p_tags) == 1
            user_href_links = [href for href in padp_p_tags[0].findAll('a', href=True)]
            assert len(user_href_links) == 1
            sellers.append(user_href_links[0].text)
            seller_urls.append(urlparse(user_href_links[0]["href"]).path)

        assert len(titles) == len(sellers) == len(col_1centres)

        return tuple(titles), tuple(sellers), tuple(seller_urls)

    @staticmethod
    def get_captcha_image_url_from_market_page(soup_html):
        image_divs = [div for div in soup_html.findAll('div', attrs={'class': 'image'})]
        assert len(image_divs) == 1
        img_tags = [img for img in image_divs[0].findAll('img')]
        assert len(img_tags) == 1
        url: str = img_tags[0]['src']
        return urlparse(url).path

    @staticmethod
    def get_category_urls_and_nr_of_listings(soup_html: BeautifulSoup) -> Tuple[Tuple[str, int]]:
        main_menu_uls = [ul for ul in soup_html.findAll('ul', attrs={'class': 'mainmenu'})]
        assert len(main_menu_uls) == 1
        main_menu_ul = main_menu_uls[0]
        lis = [li for li in main_menu_ul.findAll('li', recursive=False)]
        assert len(lis) == 11

        category_urls_and_nr_of_listings: List[Tuple[str, int]] = []

        for li in lis:
            category_url = li.find('a', href=True)["href"]
            category_url_path = urlparse(category_url).path
            nr_of_listings = li.find('span').text
            category_urls_and_nr_of_listings.append((category_url_path, nr_of_listings))

        return tuple(category_urls_and_nr_of_listings)

    @staticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:

        payload = {}

        div = soup_html.find('div', attrs={'class': 'login-textbox'})
        inputs = [input for input in div.findAll('input')]

        payload[inputs[0]['name']] = username
        payload[inputs[1]['name']] = password
        payload[inputs[2]['name']] = captcha_solution

        for input in inputs[3:]:
            input_value = input['value']
            payload[input['name']] = input_value

        return payload

    @staticmethod
    def get_seller_about_description(soup_html, seller_name):
        tab_content_divs = [div for div in soup_html.findAll('div', attrs={'class': 'tabcontent_user_feedback'})]
        assert len(tab_content_divs) == 1
        description = tab_content_divs[0].text
        index_of_seller_name = description.find(seller_name)
        description_after_standard_heading = description[index_of_seller_name + len(seller_name) + 3:]
        return shorten_and_sanitize_for_text_column(description_after_standard_heading)

    @staticmethod
    def get_seller_statistics(soup_html: BeautifulSoup) -> int:
        seller_rating_divs = [div for div in soup_html.findAll('div', attrs={'class': 'seller_rating'})]
        assert len(seller_rating_divs) == 1
        hrefs = [href for href in seller_rating_divs[0].findAll('a', href=True)]
        assert len(hrefs) == 9

        feedbacks = []

        for href in hrefs:
            feedbacks.append(int(href.text))

        assert len(feedbacks) == 9

        return feedbacks

    @staticmethod
    def get_buyer_statistics(soup_html):
        buyer_statistics_divs = [div for div in soup_html.findAll('div', attrs={'class': 'buyer_statistics'})]
        assert len(buyer_statistics_divs) == 1
        tables = [table for table in buyer_statistics_divs[0].findAll('table')]
        assert len(tables) == 1
        trs = [tr for tr in tables[0].findAll('tr')]

        tds = [td for td in trs[1].findAll('td')]
        disputes, orders = [s.strip() for s in tds[1].text.split("/")]

        tds = [td for td in trs[2].findAll('td')]
        spendings = tds[1].text

        tds = [td for td in trs[3].findAll('td')]
        td_body = tds[1].text
        td_body_parts = td_body.split(" ")
        feedback_left = td_body_parts[0]
        feedback_percent_positive = td_body_parts[1][1:-1]

        tds = [td for td in trs[4].findAll('td')]
        unparsed_date = tds[1].text
        last_online = dateparser.parse(unparsed_date)

        return disputes, orders, spendings, int(feedback_left), feedback_percent_positive, last_online

    @staticmethod
    def get_star_ratings(soup_html):
        rating_star_divs = [div for div in soup_html.findAll('div', attrs={'class': 'rating_star'})]
        assert len(rating_star_divs) == 1
        tables = [table for table in rating_star_divs[0].findAll('table')]
        assert len(tables) == 1
        trs = [tr for tr in tables[0].findAll('tr')]
        assert len(trs) == 2
        tds = [td for td in trs[1].findAll('td')]
        assert len(tds) == 5

        star_ratings = []

        for td in tds[2:]:
            star_icons = [star_icon for star_icon in td.findAll('i', attrs={'class': 'fa fa-star'})]
            star_ratings.append(len(star_icons))

        return star_ratings

    @staticmethod
    def get_feedback_categories_and_feedback_urls_and_pgp_url(soup_html: BeautifulSoup) -> Tuple[
        Tuple[str], Tuple[str], str]:
        tab_divs = [div for div in soup_html.findAll('div', attrs={'class': 'tab'})]
        assert len(tab_divs) == 1
        hrefs = [href for href in tab_divs[0].findAll('a', href=True)]
        assert len(hrefs) == 6

        feedback_categories: List[str] = []
        feedback_urls: List[str] = []

        for href in hrefs[1:5]:
            feedback_categories.append(href.text)
            feedback_url_path = urlparse(href["href"]).path
            feedback_urls.append(feedback_url_path)

        pgp_url = urlparse(hrefs[5]["href"]).path

        return tuple(feedback_categories), tuple(feedback_urls), pgp_url

    @staticmethod
    def get_feedbacks(soup_html):
        # TODO: Scrape titles of associated products
        autoshop_tables = [div for div in
                           soup_html.findAll('table', attrs={'class': 'user_feedbackTbl autoshop_table'})]
        assert len(autoshop_tables) <= 1
        if len(autoshop_tables) == 0:
            return []

        autoshop_table = autoshop_tables[0]

        feedbacks = []
        trs = [tr for tr in autoshop_table.findAll('tr')]

        for tr in trs[1:]:
            feedback = {}
            messages = [p for p in tr.findAll('p', attrs={'class': 'setp1 bold1 feedback_msg'})]
            assert len(messages) <= 2
            feedback["feedback_message"] = shorten_and_sanitize_for_text_column(messages[0].text)
            if len(messages) == 2:
                seller_response = messages[1].text.strip()
                seller_response_header_text = "Seller Response: "

                assert (seller_response[0:len(seller_response_header_text)] == seller_response_header_text)
                feedback["seller_response_message"] = shorten_and_sanitize_for_text_column(
                    seller_response[len(seller_response_header_text):])
            else:
                feedback["seller_response_message"] = ""

            buyers = [p for p in tr.findAll('font', attrs={'style': 'color:#dc6831;'})]
            assert len(buyers) == 1
            feedback["buyer"] = buyers[0].text

            mid_columns = [p for p in tr.findAll('p', attrs={'class': 'setp1 c_424648'})]
            assert len(mid_columns) == 2
            lines = mid_columns[1].text.split("\n")
            assert len(lines) == 2
            parts = lines[1].split(" ")

            feedback["currency"] = parts[-2]
            feedback["price"] = parts[-1].replace(",", "")

            # <td style="text-align: right;">
            right_columns = [td for td in tr.findAll('td', attrs={'style': 'text-align: right;'})]
            assert len(right_columns) == 1
            right_column = right_columns[0]
            ps = [p for p in right_column.findAll('p')]
            assert len(ps) == 1
            parts = ps[0].text.split("\n")
            feedback["date_published"] = dateparser.parse(parts[0])

            hrefs = [href["href"] for href in right_column.findAll('a', href=True)]
            assert len(hrefs) == 1

            feedback["product_url"] = hrefs[0]
            feedbacks.append(feedback)

        return feedbacks

    @staticmethod
    def get_mid_user_info(soup_html: BeautifulSoup) -> Tuple[float, datetime]:
        user_info_mid_divs = [div for div in soup_html.findAll('div', attrs={'class': 'user_info_mid'})]
        assert len(user_info_mid_divs) == 1
        user_info_mid_div = user_info_mid_divs[0]

        inner_divs = [div for div in user_info_mid_div.findAll('div')]
        assert len(inner_divs) == 1
        inner_div = inner_divs[0]

        bold_ps = [p for p in inner_div.findAll('p', attrs={'class': 'bold', 'style': 'padding: 0;'})]
        assert len(bold_ps) == 1
        bold_p = bold_ps[0]
        bolds = [b for b in bold_p.findAll('b')]
        assert len(bolds) == 1
        positive_feedback_received_percent = bolds[0].text
        bold_spans = [span for span in inner_div.findAll('span', attrs={'class': 'bold1'})]
        assert len(bold_spans) == 1
        registration_date = dateparser.parse(bold_spans[0].text)

        return positive_feedback_received_percent, registration_date

    @staticmethod
    def get_next_feedback_page(soup_html: BeautifulSoup) -> Optional[str]:
        pagination_uls = [ul for ul in soup_html.findAll('ul', attrs={'class': 'pagination'})]

        if len(pagination_uls) == 0:
            return None

        assert len(pagination_uls) == 1
        pagination_ul = pagination_uls[0]

        strongs = [strong for strong in pagination_ul.findAll('strong')]
        assert len(strongs) == 1
        strong = strongs[0]

        current_page = int(strong.text)

        data_ci_pagination_pages = [pagination_page for pagination_page in pagination_ul.findAll('a')]

        for pagination_page_url in data_ci_pagination_pages:
            try:
                if int(pagination_page_url.text) > current_page:
                    return urlparse(pagination_page_url["href"]).path
            except ValueError:
                pass

        return None

    @staticmethod
    def get_pgp_key(soup_html):
        tab_content_divs = [div for div in soup_html.findAll('div', attrs={'class': 'tabcontent_user_feedback'})]
        assert len(tab_content_divs) == 1
        tab_content_div = tab_content_divs[0]

        pres = [pre for pre in tab_content_div.findAll('pre')]
        assert len(pres) == 1
        pre = pres[0]

        return pre.text

    @staticmethod
    def get_external_market_ratings(soup_html: BeautifulSoup) -> Tuple[
        Tuple[Optional[str], Optional[int], Optional[float], Optional[str]]]:
        external_ratings: List[Tuple[Optional[str], Optional[int], Optional[float], Optional[str]]] = []

        user_info_mid_divs = [div for div in soup_html.findAll('div', attrs={'class': 'user_info_mid'})]
        assert len(user_info_mid_divs) == 1
        user_info_mid_div = user_info_mid_divs[0]

        inner_divs = [div for div in user_info_mid_div.findAll('div')]
        assert len(inner_divs) == 1
        inner_div = inner_divs[0]

        spans = [span for span in inner_div.findAll('span')]
        if len(spans) > 0:
            titled_spans = [span for span in spans if
                            "title" in span.attrs.keys() and span.attrs["title"].find("Verified") != -1]
            remaining_external_market_ratings = list(EMPIRE_MARKET_EXTERNAL_MARKET_STRINGS)
            for titled_span in titled_spans:
                ext_market_rating = _parse_external_market_rating(titled_span, remaining_external_market_ratings)
                if ext_market_rating:
                    market_id, sales, rating, remaining_external_market_ratings = ext_market_rating
                    free_text = None
                else:
                    market_id, sales, rating, free_text = (None, None, None, titled_span.text)

                external_ratings.append((market_id, sales, rating, free_text))

        return tuple(external_ratings)

    @staticmethod
    def get_product_class_quantity_left_and_ends_in(soup_html: BeautifulSoup) -> Tuple[str, int, str]:
        product_class: str
        quantity_left: Optional[int]
        ends_in: str

        product_class_table_row = soup_html.select_one("table.productTbl > tbody:nth-child(2) > tr:nth-child(1)")
        quantity_left_table_row = soup_html.select_one("table.productTbl > tbody:nth-child(2) > tr:nth-child(2)")
        ends_in_table_row = soup_html.select_one("table.productTbl > tbody:nth-child(2) > tr:nth-child(3)")

        assert product_class_table_row.select_one("td:nth-child(1)").text == "Product Class"
        assert quantity_left_table_row.select_one("td:nth-child(1)").text == "Quantity Left"
        assert ends_in_table_row.select_one("td:nth-child(1)").text == "Ends In"

        product_class = product_class_table_row.select_one("td:nth-child(2)").text
        quantity_text = quantity_left_table_row.select_one("td:nth-child(2)").text.strip()
        quantity_left = int(quantity_text) if quantity_text != "Unlimited" else None
        ends_in = ends_in_table_row.select_one("td:nth-child(2)").text

        return product_class, quantity_left, ends_in

    @staticmethod
    def has_unlimited_dispatch_and_quantity_in_stock(soup_html) -> Tuple[bool, Optional[int]]:
        italic_text_box = soup_html.select_one(".listDes > p:nth-child(3) > i:nth-child(7)")
        if italic_text_box:
            if italic_text_box.text == "Unlimited items available for auto-dispatch":
                return True, None
            else:
                quantity_in_stock = parse_int(italic_text_box.text.split(maxsplit=1)[0])
                return True, quantity_in_stock
        else:
            return False, None

    @staticmethod
    def get_nrs_of_views(soup_html: BeautifulSoup) -> Tuple[int]:
        nrs_of_views: List[int] = []
        pattern = "Views:"
        head_div: BeautifulSoup

        head_divs = soup_html.select("div.col-1search > div:nth-child(2) > div:nth-child(1)")
        assert len(head_divs) <= ASSUMED_MAXIMUM_LISTINGS_PER_SEARCH_RESULT
        assert len(head_divs) > 0
        for head_div in head_divs:
            pattern_index = head_div.text.find(pattern)
            assert pattern_index != -1
            relative_slash_index = head_div.text[pattern_index + len(pattern):].find("/")
            start_index = pattern_index + len(pattern)
            end_index = pattern_index + len(pattern) + relative_slash_index
            nr_of_views = parse_int(head_div.text[start_index:end_index])
            nrs_of_views.append(nr_of_views)

        return tuple(nrs_of_views)

    @staticmethod
    def get_shipping_methods(soup_html: BeautifulSoup) -> Tuple[Tuple[str, float, str, float, Optional[str], bool]]:

        shipping_methods: List[Tuple[str, float, str, float, Optional[str], bool]] = []

        options = soup_html.select("select.productTbl > option")
        option: BeautifulSoup
        for option in options:
            description, shipping_time, price_string = [s.strip() for s in option.text.split("-")]
            timedelta_val = parse_time_delta_from_string(shipping_time)
            days_shipping_time: float = timedelta_val.total_seconds() / ONE_DAY
            fiat_currency_and_price_per_unit = price_string.split("+")
            fiat_currency = fiat_currency_and_price_per_unit[0].strip()
            assert len(fiat_currency) == CURRENCY_COLUMN_LENGTH
            price_and_is_per_unit = fiat_currency_and_price_per_unit[1].split("/")
            if len(price_and_is_per_unit) == 1:
                price_is_per_unit = False
                quantity_unit_name = None
            elif len(price_and_is_per_unit) == 2:
                price_is_per_unit = True
                quantity_unit_name = price_and_is_per_unit[1].strip()
            else:
                raise AssertionError(f"Unknown format in {option.text}")
            price = parse_float(price_and_is_per_unit[0])
            shipping_methods.append(
                (description, days_shipping_time, fiat_currency, price, quantity_unit_name, price_is_per_unit))

        return tuple(shipping_methods)

    @staticmethod
    def get_bulk_prices(soup_html: BeautifulSoup) -> Tuple[Tuple[int, Optional[int], float, float, Optional[float]]]:


        bulk_prices: List[Tuple[int, Optional[int], float, float, Optional[float]]] = []

        bulk_table_rows = soup_html.select(
            "body > div:nth-child(2) > div.body-content > div.wrapper-index > div.right-content > div:nth-child(1) > "
            "div.listDes > table:nth-child(7) > tbody > tr")

        table_row: BeautifulSoup
        for table_row in bulk_table_rows:
            tds = table_row.select("td")
            assert len(tds) == 4
            quantity_range_string_parts = tds[1].text.split()
            assert len(quantity_range_string_parts) == 5
            lower_bound = parse_int(quantity_range_string_parts[2])
            upper_bound = parse_int(quantity_range_string_parts[4])
            fiat_currency, unparsed_fiat_price = tds[2].text.strip().split()
            fiat_price = parse_float(unparsed_fiat_price)
            unparsed_bulk_btc_price, crypto_currency = tds[3].text.strip().split()
            bulk_btc_price = parse_float(unparsed_bulk_btc_price)
            bulk_prices.append((lower_bound, upper_bound, fiat_price, bulk_btc_price, None))

        return tuple(bulk_prices)

    @staticmethod
    def user_is_banned(soup_html: BeautifulSoup) -> bool:
        span: BeautifulSoup = soup_html.select_one(
            "body > div:nth-child(2) > div.body-content > div.wrapper-index > div.right-content > h1 > span")
        return span.text == "(BANNED)"
