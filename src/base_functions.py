from abc import abstractstaticmethod
from datetime import datetime
from time import time
from typing import Tuple, Optional, List, Dict

import bs4
import dateparser
from bs4 import BeautifulSoup
from src.base_logger import BaseClassWithLogger


def _find_index_of_h4_with_market_string(h4s: List[BeautifulSoup], market_string: str,
                                         content_soup: BeautifulSoup) -> int:
    for h4 in h4s:
        a_href_tags = [a_tag for a_tag in h4.findAll('a', href=True)]
        assert len(a_href_tags) == 1
        if a_href_tags[0].text.strip() == market_string:
            return content_soup.contents.index(h4)

    raise AssertionError(f"Mirror for market with string {market_string} not found in h4 headings.")


def _find_index_of_next_h_tag(start_index: int, content_soup: BeautifulSoup) -> int:
    if start_index == len(content_soup.contents) - 1:
        return len(content_soup.contents)

    soup: BeautifulSoup

    for i, soup in zip(range(start_index + 1, len(content_soup)), content_soup.contents[start_index + 1:]):
        if soup.name == "h4":
            a_href_tags = [a_tag for a_tag in soup.findAll('a', href=True)]
            assert len(a_href_tags) == 1
            return i
        elif soup.name == "h3":
            return i

    raise AssertionError('Could not find index of next h_tag')


def _get_recursive_divs_between_start_and_end(start_index: int, end_index: int, content_soup: BeautifulSoup) -> Tuple[
    BeautifulSoup]:
    soup: BeautifulSoup
    divs: List[BeautifulSoup] = []
    for soup in content_soup.contents[start_index:end_index]:
        if isinstance(soup, bs4.element.Tag):
            if soup.name == "div":
                divs += [soup]
            divs += [div for div in soup.findAll('div')]

    return tuple(divs)


def _find_market_div_with_sub_url(start_index: int, end_index: int, content_soup: BeautifulSoup) -> Optional[
    BeautifulSoup]:
    divs: List[BeautifulSoup] = _get_recursive_divs_between_start_and_end(start_index, end_index, content_soup)

    market_divs_with_sub_url = [div for div in divs if "class" in div.attrs.keys() and div.attrs["class"] == ["more"]]

    if len(market_divs_with_sub_url) == 0:
        return None
    elif len(market_divs_with_sub_url) == 1:
        return market_divs_with_sub_url[0]
    else:
        raise AssertionError('Found more than one sub url.')


def _get_divs_between_start_and_end(start_index: int, end_index: int, content_soup: BeautifulSoup) -> Tuple[
    BeautifulSoup]:
    divs: List[BeautifulSoup] = []
    soup: BeautifulSoup
    for soup in content_soup.contents[start_index:end_index]:
        if soup.name == "div":
            divs.append(soup)

    return tuple(divs)


def _find_lis_with_mirrors(start_index: int, end_index: int, content_soup: BeautifulSoup) -> Tuple[BeautifulSoup]:
    divs: List[BeautifulSoup] = _get_divs_between_start_and_end(start_index, end_index, content_soup)

    div: BeautifulSoup
    visible_divs = [div for div in divs if "class" in div.attrs.keys() and div.attrs["class"] != ["fud"]]

    lis: List[BeautifulSoup] = []
    for div in visible_divs:
        lis += [li for li in div.findAll('li')]

    return tuple(lis)


class BaseFunctions(BaseClassWithLogger):

    @abstractstaticmethod
    def get_captcha_image_url_from_market_page(soup_html: BeautifulSoup) -> str:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_meta_refresh_interval(soup_html: BeautifulSoup) -> Tuple[int, str]:
        pass

    @staticmethod
    def get_sub_url_with_all_market_mirrors(soup_html: BeautifulSoup, market_string: str) -> Optional[str]:
        content_soups = soup_html.select(".content")
        assert len(content_soups) == 1
        content_soup: BeautifulSoup = content_soups[0]
        h4s = [h4 for h4 in content_soup.findAll('h4')]
        index_of_h4_with_market_string: int = _find_index_of_h4_with_market_string(h4s, market_string, content_soup)
        index_of_next_h4: int = _find_index_of_next_h_tag(index_of_h4_with_market_string, content_soup)
        div_with_sub_url = _find_market_div_with_sub_url(index_of_h4_with_market_string, index_of_next_h4, content_soup)

        if div_with_sub_url:
            a_href_tags = [a_tag for a_tag in div_with_sub_url.findAll('a', href=True)]
            if len(a_href_tags) == 0:
                return None
            elif len(a_href_tags) == 1:
                return a_href_tags[0]["href"]
            else:
                raise AssertionError('Unknown format in "more"-classed div.')
        else:
            return None

    @staticmethod
    def get_market_mirrors_from_final_page(soup_html: BeautifulSoup) -> Dict[str, float]:
        urls_divs = soup_html.select(".urls")
        assert len(urls_divs) == 1
        url_div: BeautifulSoup = urls_divs[0]

        table_rows = [tr for tr in url_div.findAll('tr')]

        res_dict: Dict[str, float] = {}
        pattern = "- Last Online: Sat "
        pattern_length = len(pattern)
        url_schema_pattern = "://"

        table_row: BeautifulSoup
        for table_row in table_rows:
            td: BeautifulSoup
            table_datas = [td for td in table_row.findAll('td') if "class" in td.attrs.keys()]
            assert len(table_datas) == 1
            table_data = table_datas[0]
            url = table_data.contents[1].text
            pattern_index = url.find(url_schema_pattern)
            if pattern_index != -1:
                cleaned_url = url[pattern_index+len(url_schema_pattern):]
            else:
                cleaned_url = url

            if table_data.attrs["class"] in [['url', 'status2'], ['url', 'status0']]:
                last_online_phrase: str = table_data.contents[3].text
                last_online_string: str = last_online_phrase[pattern_length:]
                last_online_datetime: datetime = dateparser.parse(last_online_string)
                last_online_timestamp: float = datetime.timestamp(last_online_datetime)
                res_dict[cleaned_url] = last_online_timestamp
            elif table_data.attrs["class"] == ['url', 'status1']:
                res_dict[cleaned_url] = time()
            else:
                raise AssertionError("Unknown formatting on list of urls in final page of mirror overview site.")

        return res_dict

    @staticmethod
    def get_market_mirrors_from_main_page(soup_html: BeautifulSoup, market_string: str) -> Dict[str, float]:
        content_soups = soup_html.select(".content")
        assert len(content_soups) == 1
        content_soup: BeautifulSoup = content_soups[0]
        h4s = [h4 for h4 in content_soup.findAll('h4')]
        index_of_h4_with_market_string: int = _find_index_of_h4_with_market_string(h4s, market_string, content_soup)
        index_of_next_h4: int = _find_index_of_next_h_tag(index_of_h4_with_market_string, content_soup)

        lis = _find_lis_with_mirrors(index_of_h4_with_market_string, index_of_next_h4, content_soup)

        market_mirrors: Dict[str, float] = {}
        pattern = "://"
        li: BeautifulSoup
        for li in lis:
            url = li.find('code').text
            pattern_index = url.find(pattern)
            if pattern_index != -1:
                cleaned_url = url[pattern_index + len(pattern):]
            else:
                cleaned_url = url
            if li.attrs["class"][-1] == "status0":
                market_mirrors[cleaned_url] = 0  # offline
            elif li.attrs["class"][-1] == "status1":
                market_mirrors[cleaned_url] = time()  # online
            elif li.attrs["class"][-1] == "status2":
                market_mirrors[cleaned_url] = 0  # offline
            else:
                raise AssertionError("Unkonwn list item format.")

        return market_mirrors

    @staticmethod
    def get_captcha_page_url(soup_html: BeautifulSoup) -> str:
        a_tags = soup_html.select("body > div.content > p:nth-child(5) > a")
        assert len(a_tags) == 1
        a_tag = a_tags[0]

        assert a_tag.text == "view all links"
        return a_tag["href"]

    @staticmethod
    def get_captcha_base64_image_from_mirror_overview_page(soup_html: BeautifulSoup) -> str:
        imgs = [img for img in soup_html.findAll('img')]
        assert len(imgs) == 1
        img = imgs[0]

        pattern = "data:data:image/png;base64,"

        return img["src"][len(pattern):]

    @staticmethod
    def get_captcha_solution_payload_to_mirror_overview_page(soup_html: BeautifulSoup, captcha_solution: str) -> Dict[
        str, str]:
        id_inputs = [input for input in soup_html.findAll('input') if
                     'name' in input.attrs and input.attrs["name"] == 'id']
        assert len(id_inputs) == 1
        id_input = id_inputs[0]
        id = id_input["value"]

        return {'id': id, 'captcha': captcha_solution}

    @staticmethod
    def captcha_solution_was_wrong(soup_html: BeautifulSoup) -> bool:
        ps = [p for p in soup_html.findAll('p')]

        p: BeautifulSoup
        for p in ps:
            keys = [key for key in p.attrs.keys()]
            if "style" in keys and p["style"] == "color: red;" and p.text == "Incorrect CAPTCHA.":
                return True

        return False

    @staticmethod
    def get_captcha_solution_post_url(soup_html: BeautifulSoup) -> str:
        forms = [form for form in soup_html.findAll('form') if
                 'method' in form.attrs and form.attrs["method"] == 'post']
        assert len(forms) == 1
        form = forms[0]
        post_url = form["action"]

        return post_url

    @staticmethod
    def get_stylesheet_url_from_arbitrary_mirror_overview_site_page(soup_html: BeautifulSoup) -> Optional[str]:
        head: BeautifulSoup = soup_html.select_one("head")
        link: BeautifulSoup
        if not head:
            return
        links = [link for link in head.findAll('link') if
                 'rel' in link.attrs.keys() and link.attrs["rel"] == ["stylesheet"] and 'href' in link.attrs.keys()]
        assert len(links) <= 1
        if links:
            return links[0]["href"]
