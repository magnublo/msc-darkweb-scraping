import re
from abc import abstractstaticmethod
from datetime import datetime
from time import time
from typing import Tuple, Optional, List, Dict, Set

import bs4
import dateparser
from bs4 import BeautifulSoup
from src.base.base_logger import BaseClassWithLogger
import cssutils

from src.utils import parse_int, parse_float


def _find_index_of_h4_with_market_string(h4s: List[BeautifulSoup], market_string: str,
                                         content_soup: BeautifulSoup) -> Optional[int]:
    for h4 in h4s:
        a_href_tags = [a_tag for a_tag in h4.findAll('a', href=True)]
        if len(a_href_tags) == 1:
            if a_href_tags[0].text.strip() == market_string:
                return content_soup.contents.index(h4)
        elif len(a_href_tags) == 0:
            continue
        else:
            raise AssertionError(f'Expected 1 or 2 hrefs in {h4}')


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
    COMMA_SEPARATED_COUNTRY_REGEX = re.compile(r"([^,])+(,(\s+[a-zA-Z]+)+(\s+of))?")

    @abstractstaticmethod
    def is_logged_in(soup_html: BeautifulSoup, username: str) -> bool:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_captcha_image_url_from_market_page(soup_html: BeautifulSoup) -> str:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_login_payload(soup_html: BeautifulSoup, username: str, password: str, captcha_solution: str) -> dict:
        raise NotImplementedError('')

    @abstractstaticmethod
    def get_meta_refresh_interval(soup_html: BeautifulSoup) -> Tuple[int, str]:
        pass

    @abstractstaticmethod
    def get_captcha_instruction(soup_html: BeautifulSoup) -> str:
        pass

    @staticmethod
    def get_sub_url_with_all_market_mirrors(soup_html: BeautifulSoup, market_string: str) -> Optional[str]:
        content_soups = soup_html.select(".content")
        assert len(content_soups) == 1
        content_soup: BeautifulSoup = content_soups[0]
        h4s = [h4 for h4 in content_soup.findAll('h4')]
        index_of_h4_with_market_string: int = _find_index_of_h4_with_market_string(h4s, market_string, content_soup)
        if not index_of_h4_with_market_string:
            return None
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
                cleaned_url = url[pattern_index + len(url_schema_pattern):]
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
        if not index_of_h4_with_market_string:
            return {}
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
    def _get_invisible_classes(soup_html: BeautifulSoup) -> Tuple[str]:
        styles = soup_html.select("head > style")
        assert len(styles) == 1
        style = styles[0]

        style: BeautifulSoup
        sheet = cssutils.parseString(style.text)

        # finding all HTML classes with CSS attribute 'display' set to 'none'
        invisible_classes = [str(s.selectorText.split(".")[-1]) for s in sheet if s.style.display == "none"]

        return tuple(invisible_classes)

    @staticmethod
    def get_captcha_base64_image_from_mirror_overview_page(soup_html: BeautifulSoup) -> str:
        all_imgs = set([img for img in soup_html.findAll('img')])

        # finding all images which are invisible in a typical browser
        invisible_imgs = BaseFunctions._get_invisible_html_elements(soup_html, all_imgs)

        captcha_imgs = all_imgs.difference(invisible_imgs)

        assert len(captcha_imgs) == 1
        captcha_img = next(iter(captcha_imgs))

        pattern = "data:data:image/png;base64,"
        base64_image = captcha_img["src"][len(pattern):]

        return base64_image

    @staticmethod
    def get_captcha_post_parameter_name(soup_html: BeautifulSoup) -> str:
        all_input_fields = set(soup_html.select("body > div.content > form > input[type=text]"))
        invisible_input_fields = BaseFunctions._get_invisible_html_elements(soup_html, all_input_fields)

        visible_captcha_input_fields = all_input_fields.difference(invisible_input_fields)
        assert len(visible_captcha_input_fields) == 1
        visible_captcha_input_field = next(iter(visible_captcha_input_fields))

        name_of_captcha_post_parameter = visible_captcha_input_field['name']

        return name_of_captcha_post_parameter

    @staticmethod
    def get_captcha_solution_payload_to_mirror_overview_page(soup_html: BeautifulSoup, captcha_solution: str,
                                                             captcha_parameter_name: str, captcha_id_parameter_name: str) -> Dict[
        str, str]:
        id_inputs = [input for input in soup_html.findAll('input') if
                     'name' in input.attrs and input.attrs["name"] == captcha_id_parameter_name]
        assert len(id_inputs) == 1
        id_input = id_inputs[0]
        id = id_input["value"]

        return {captcha_id_parameter_name: id, captcha_parameter_name: captcha_solution}

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

    @staticmethod
    def get_captcha_id_parameter_name(soup_html: BeautifulSoup) -> str:
        inputs = soup_html.select("body > div.content > form > input[type=hidden]")

        for html_input in inputs:
            if "value" in html_input.attrs.keys() and len(html_input.attrs["value"]) > 3:
                return html_input["name"]

        raise AssertionError("Could not find ID parameter.")

    @staticmethod
    def _get_invisible_html_elements(soup_html: BeautifulSoup, all_elements: Set[BeautifulSoup]) -> Set[BeautifulSoup]:
        invisible_classes = BaseFunctions._get_invisible_classes(soup_html)
        invisible_elements = set()
        for element in all_elements:
            element_classes = element.attrs.get("class")
            if element_classes:
                for element_class in element_classes:
                    if element_class in invisible_classes:
                        invisible_elements.add(element)
            img_style = element.attrs.get("style")
            if img_style and img_style.replace(" ", "")[0:12] == "display:none":
                invisible_elements.add(element)

        return invisible_elements


def get_external_rating_tuple(market_id: str, info_string: str) -> Tuple[
    str, Optional[int], Optional[float], Optional[float], Optional[int], Optional[int], Optional[int], Optional[str]]:
    sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text = (
        None, None, None, None, None, None, None)

    if info_string == "":
        pass  # empty string
        free_text = "No seller stats associated with this verification."
    elif re.match(r"^\d+\/\d+\/\d+$", info_string):
        pass  # good neutral bad tuple, 11/2/44
        good_reviews, neutral_reviews, bad_reviews = [int(a) for a in info_string.split("/")]
    elif re.match(r"^\d+,?\d+\+?\s+deals,?\s+\d+(\.\d+)*\/\d+(\.\d+)*%?$", info_string):
        pass  # deals tuple, sales nr is lower estimate, '123 deals, 2.44/5'
        whitespace_parts = info_string.split()
        if whitespace_parts[0][-1] == "+":
            free_text = 'nr of sales is lower estimate'
        slash_parts = whitespace_parts[-1].split("/")
        sales, rating, max_rating = (parse_int(whitespace_parts[0]), float(slash_parts[0]), parse_float(slash_parts[1]))
    elif re.match(r"^\d+,?\d+\+?\s+deals,?\s+\d+(\.\d+)*$", info_string):
        pass  # deals tuple, sales nr is lower estimate, '123 deals, 2.44'
        whitespace_parts = info_string.split()
        slash_parts = whitespace_parts[-1].split("/")
        sales, rating = (parse_int(whitespace_parts[0]), float(slash_parts[0]))
    elif re.match(r"^\d+(\.\d+)*\/\d+(\.\d+)*$", info_string):
        pass  # rating, max_rating tuple, '2.44/5'
        rating, max_rating = [float(f) for f in info_string.split("/")]
    elif re.match(r"^\d+,?\d+\s+\d+(\.\d+)*\/\d+(\.\d+)*$", info_string):
        pass  # sales, rating, max_rating tuple, '123 2.44/5'
        parts = re.split(r"\s+|\/", info_string)
        sales, rating, max_rating = (int(parts[0]), float(parts[1]), float(parts[2]))
    elif re.match(r"^\d+,?\d+\s+ deals,?$", info_string):
        pass  # sales, '123 deals'
        sales = int(info_string.split()[0])
    elif re.match(r"^\d+,?\d+$", info_string):
        pass  # sales without deals keyword, 123
        sales = int(info_string)
    elif re.match(r"^\d+\.\d+$", info_string):
        pass  # rating only
        rating = float(info_string)
    elif re.match(r"^\d+,?\d+\+?~\d+,?\d+\+?\s+deals,?\s+\d+(\.\d+)*\/\d+(\.\d+)*%?$", info_string):
        pass  # deals tuple, sales is a range, '12~22 deals, 2.44/5'
        whitespace_parts = info_string.split()
        lower_bound, upper_bound = [parse_int(i) for i in whitespace_parts[0].split("~")]
        free_text = f"Sales is somewhere between {lower_bound} and {upper_bound}."
        slash_parts = whitespace_parts[-1].split("/")
        sales, rating, max_rating = (
        int(sum((upper_bound, lower_bound)) / 2), float(slash_parts[0]), parse_float(slash_parts[1]))
    elif re.match(r"([0-9]+)\s\(([0-9\,\.]+)\)", info_string):
        pass  # 1400 (4.96)
        re_match = re.match(r"([0-9]+)\s\(([0-9\,\.]+)\)", info_string)
        sales = parse_int(info_string[re_match.regs[1][0]:re_match.regs[1][1]])
        rating = parse_float(info_string[re_match.regs[2][0]:re_match.regs[2][1]])
    elif re.match(r"([0-9]+)\sSales\s\|\s([0-9]+)\/([0-9]+)\/([0-9]+)", info_string):
        pass  # 410 Sales | 350/4/0
        re_match = re.match(r"([0-9]+)\sSales\s\|\s([0-9]+)\/([0-9]+)\/([0-9]+)", info_string)
        sales = parse_int(info_string[re_match.regs[1][0]:re_match.regs[1][1]])
        good_reviews = parse_int(info_string[re_match.regs[2][0]:re_match.regs[2][1]])
        neutral_reviews = parse_int(info_string[re_match.regs[3][0]:re_match.regs[3][1]])
        bad_reviews = parse_int(info_string[re_match.regs[4][0]:re_match.regs[4][1]])
    elif re.match(r"([0-9]+)\sSales\s\(([0-9]{1,2})%\)$", info_string):
        re_match = re.match(r"([0-9]+)\sSales\s\(([0-9]{1,2})%\)$", info_string)
        sales = parse_int(info_string[re_match.regs[1][0]:re_match.regs[1][1]])
        rating = parse_float(info_string[re_match.regs[2][0]:re_match.regs[2][1]])
        pass  # 47 Sales (91%)
    else:
        free_text = info_string

    return market_id, sales, rating, max_rating, good_reviews, neutral_reviews, bad_reviews, free_text