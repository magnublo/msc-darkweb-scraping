import json
import time
from datetime import datetime

import dateparser as dateparser

from definitions import MYSQL_TEXT_COLUMN_MAX_LENGTH
from src.base import BaseFunctions


def _shorten_for_text_column(description):
    mxlen = MYSQL_TEXT_COLUMN_MAX_LENGTH

    while (description.encode("utf8")[mxlen - 1] & 0xc0 == 0xc0):
        mxlen -= 1

    return description.encode("utf8")[0:mxlen].decode("utf8")


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
        return _shorten_for_text_column(description)


    @staticmethod
    def get_product_page_urls(soup_html):
        centre_columns = [div for div in soup_html.findAll('div', attrs={'class': 'col-1centre'})]
        product_page_urls = []
        urls_is_sticky = []

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
            product_page_urls.append(hrefs[0]['href'])

        assert len(product_page_urls) <= 15
        assert len(product_page_urls) > 0
        assert len(urls_is_sticky) == len(product_page_urls)

        return product_page_urls, urls_is_sticky

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
        text = text[pattern_index+len(pattern):]
        currency, price = text.split(" ")
        price = price.replace(",","")
        return currency, price

    @staticmethod
    def get_origin_country_and_destinations(soup_html):
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
        origin_country = td.text

        tr = trs[1]
        tds = [td for td in tr.findAll('td')]
        assert len(tds) == 4
        td = tds[3]
        destinations = [destination.strip() for destination in td.text.split(",")]

        return origin_country, destinations

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
    def get_vendor_and_trust_level(soup_html):
        list_descriptions = [div for div in soup_html.findAll('div', attrs={'class': 'listDes'})]
        assert len(list_descriptions) == 1
        list_description = list_descriptions[0]
        spans = []
        vendor_level = None
        trust_level = None

        for i in range(0, 20):
            className = "levelSet level-"+str(i)
            spans = spans + [span for span in list_description.findAll('span', attrs={'class': className})]
            if len(spans) > 0:
                for span in spans:
                    if span.text.find("Vendor") >= 0:
                        vendor_level = span.text.split(" ")[2]
                    if span.text.find("Trust") >= 0:
                        trust_level = span.text.split(" ")[2]
                    if vendor_level is not None and trust_level is not None:
                        return vendor_level, trust_level

        assert False

    @staticmethod
    def get_categories_and_ids(soup_html):
        divs = [div for div in soup_html.findAll('div', attrs={'class': 'sub_head_inner_header'})]

        assert len(divs) == 1

        a_tags = [a_tag for a_tag in divs[0].findAll('a', href=True)]

        categories = []
        category_ids = []

        for a_tag in a_tags:
            category = a_tag.text
            url = str(a_tag['href'])
            url_fragments = url.split("/")
            category_id = url_fragments[-2]
            categories.append(category)
            category_ids.append(category_id)

        assert len(category_ids) == len(categories)

        return categories, category_ids

    @staticmethod
    def get_titles_and_sellers(soup_html):
        titles = []
        sellers = []
        seller_urls = []

        col_1centres = [div for div in soup_html.findAll('div', attrs={'class': 'col-1centre'})]
        assert len(col_1centres) <= 15
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
            seller_urls.append(user_href_links[0]["href"])

        assert len(titles) == len(sellers) == len(col_1centres)

        return titles, sellers, seller_urls

    @staticmethod
    def get_captcha_image_url(soup_html):
        image_divs = [div for div in soup_html.findAll('div', attrs={'class': 'image'})]
        assert len(image_divs) == 1
        img_tags = [img for img in image_divs[0].findAll('img')]
        assert len(img_tags) == 1
        return img_tags[0]['src']

    @staticmethod
    def get_category_urls_and_nr_of_listings(soup_html):
        main_menu_uls = [ul for ul in soup_html.findAll('ul', attrs={'class': 'mainmenu'})]
        assert len(main_menu_uls) == 1
        main_menu_ul = main_menu_uls[0]
        lis = [li for li in main_menu_ul.findAll('li', recursive=False)]
        assert len(lis) == 11

        category_urls_and_nr_of_listings = []

        for li in lis:
            url = li.find('a', href=True)["href"]
            url_fragments = url.split("/")
            category_url = "/".join(url_fragments[:-1]) + "/"
            nr_of_listings = li.find('span').text
            category_urls_and_nr_of_listings.append([category_url, nr_of_listings])

        return category_urls_and_nr_of_listings

    @staticmethod
    def get_login_payload(soup_html, username, password, captcha_solution):

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
    def print_duplicate_debug_message(existing_listing_observation, initial_queue_size, queue_size, thread_id, cookie, parsing_time):
        print(datetime.fromtimestamp(time.time()))
        print("Last web response was parsed in " + str(parsing_time) + " seconds.")
        print("Database already contains listing with this seller and title for this session.")
        print("Seller: " + existing_listing_observation.seller)
        print("Listing title: " + existing_listing_observation.title)
        print("Duplicate listing, skipping...")
        print("Thread nr. " + str(thread_id))
        print("Web session " + cookie)
        print("Crawling listing nr " + str(initial_queue_size - queue_size) + " this session. ")
        print("Listings left, approximate: " + str(queue_size) + ".")
        print("\n")

    @staticmethod
    def print_crawling_debug_message(product_page_url, initial_queue_size, queue_size, thread_id, cookie, parsing_time):
        print(datetime.fromtimestamp(time.time()))
        print("Last web response was parsed in " + str(parsing_time) + " seconds.")
        print("Trying to fetch URL: " + product_page_url)
        print("Thread nr. " + str(thread_id))
        print("Web session " + cookie)
        print("Crawling listing nr " + str(initial_queue_size-queue_size) + " this session. ")
        print("Listings left, estimate: " + str(queue_size) + ".")
        print("\n")

    @staticmethod
    def get_seller_about_description(soup_html):
        tab_content_divs = [div for div in soup_html.findAll('div', attrs={'class': 'tabcontent_user_feedback'})]
        assert len(tab_content_divs) == 1
        description = tab_content_divs[0].text
        return _shorten_for_text_column(description)

    @staticmethod
    def get_seller_statistics(soup_html):
        pass

    @staticmethod
    def get_buyer_statistics(soup_html):
        pass

    @staticmethod
    def get_star_ratings(soup_html):
        pass
