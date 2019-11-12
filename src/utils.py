import inspect
import re
from datetime import datetime, timedelta
from enum import Enum
from time import time, sleep
from typing import Tuple, List, Dict, Optional, Callable

import brotli
import pycountry
import requests
from bs4 import BeautifulSoup
from text2digits import text2digits
from urllib3.exceptions import HTTPError

from definitions import BEAUTIFUL_SOUP_HTML_PARSER, MARKET_IDS, MAX_MARKET_THREADS_PER_PROXY, \
    ONE_DAY, ONE_WEEK, ONE_HOUR, WEB_EXCEPTIONS_TUPLE, MIRROR_TEST_TIMEOUT_LIMIT, NR_OF_TRIES_PER_MIRROR
from src.data.continent_dict import CONTINENT_DICTIONARY
from src.data.country_dict import COUNTRY_DICT
from src.exceptions import EmptyResponseException, BadGatewayException, InternalServerErrorException, \
    GatewayTimeoutException
from src.tor_proxy_check import get_proxy_dict


class ListingType(Enum):
    PHYSICAL = 1,
    AUTO_DIGITAL = 2,
    MANUAL_DIGITAL = 3


def pretty_print_GET(req) -> str:
    return '{}\n{}\r\n{}\r\n\r'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items())
    )


def pretty_print_POST(req) -> str:
    return '{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    )


def error_is_sqlalchemy_error(error_string) -> bool:
    return error_string.find("site-packages/sqlalchemy") != -1 \
           or error_string.find("\'NoneType\' object has no attribute \'have_result_set\'") != -1 \
           or error_string.find("MySQL") != -1


def print_error_to_file(market_id: str, thread_id: int, error_string: str, file_postfix=None) -> None:
    file_name = f"{market_id}_thread_{thread_id}_error"
    if file_postfix:
        file_name = f"{file_name}_{file_postfix}"
    file = open(file_name, "w")
    file.write(error_string)
    file.close()


def get_error_string(scraping_object, error_traceback, sys_exec_info) -> str:
    time_of_error = str(datetime.fromtimestamp(time()))
    tb_last = sys_exec_info[2]
    func_name = str(inspect.getinnerframes(tb_last)[0][3])
    local_variable_strings = ["[" + func_name + "()]" + str(key) + ": " + str(tb_last.tb_frame.f_locals[key]) for key in
                              tb_last.tb_frame.f_locals.keys()]
    while tb_last.tb_next:
        tb_last = tb_last.tb_next
        func_name = str(inspect.getinnerframes(tb_last)[0][3])
        local_variable_strings = local_variable_strings + [
            "[" + func_name + "()]" + str(key) + ": " + str(tb_last.tb_frame.f_locals[key])
            for key in
            tb_last.tb_frame.f_locals.keys()]

    object_variables = vars(scraping_object)
    object_variable_strings = [str(key) + ": " + str(object_variables[key]) for key in object_variables.keys()]
    return "\n\n\n".join([time_of_error] + [error_traceback] + local_variable_strings + object_variable_strings)


def get_temporary_server_error(response) -> Optional[HTTPError]:
    if is_internal_server_error(response):
        return InternalServerErrorException(response.text)
    elif is_bad_gateway(response):
        return BadGatewayException(response.text)
    elif is_gateway_timed_out(response):
        return GatewayTimeoutException(response.text)
    elif is_empty_response(response):
        return EmptyResponseException()
    else:
        return None


def response_history_contains_code(response: requests.Response, response_code: int) -> bool:
    if response.status_code == response_code:
        return True

    for history_response in response.history:
        if history_response.status_code == response_code:
            return True

    return False


def is_empty_response(response: requests.Response) -> bool:
    return response.request.method == 'GET' and response.status_code == 200 and response.text.strip() == ""


def is_gateway_timed_out(response) -> bool:
    return response_history_contains_code(response, 504)


def is_bad_gateway(response: requests.Response) -> bool:
    return response_history_contains_code(response, 502)


def is_internal_server_error(response: requests.Response) -> bool:
    return response_history_contains_code(response, 500)


def queue_is_empty(queue) -> bool:
    is_empty = queue.empty()
    sleep(100)  # Must be sure that queue is indeed empty.
    return queue.empty() and is_empty


def get_page_as_soup_html(web_response_text: str) -> BeautifulSoup:
    return BeautifulSoup(web_response_text, features=BEAUTIFUL_SOUP_HTML_PARSER)


def get_logger_name(cls: object) -> str:
    class_name = cls if type(cls) == str else cls.__name__
    capital_letter_indices = [i.start(0) for i in re.finditer(r"[A-Z]", class_name)]
    unshortened_name_parts = [class_name[i:j] for i, j in
                              zip(capital_letter_indices, capital_letter_indices[1:] + [None])]
    name_parts = []
    for unshortened_name_part in unshortened_name_parts:
        name_parts.append(unshortened_name_part[:min(3, len(unshortened_name_part))])
    return "".join(name_parts)


def get_seconds_until_midnight(utc_next_midnight_datetime: datetime = None) -> float:
    if not utc_next_midnight_datetime:
        utc_next_midnight_datetime = get_utc_datetime_next_midnight()

    return (utc_next_midnight_datetime - datetime.utcnow()).total_seconds()


def get_utc_datetime_next_midnight() -> datetime:
    utc_current_datetime = datetime.fromtimestamp(datetime.utcnow().timestamp())

    utc_next_day_datetime = utc_current_datetime + timedelta(days=1)

    utc_next_day_date = utc_next_day_datetime.date()

    return datetime(year=utc_next_day_date.year, month=utc_next_day_date.month,
                    day=utc_next_day_date.day)


def get_proxies(web_site_thread_counts: Tuple[int, ...], available_proxy_ports: List[int]) -> Tuple[Tuple[dict], ...]:
    proxies = []
    total_thread_count = 0

    for thread_count in web_site_thread_counts:
        proxies_for_web_site: List[dict] = []
        for i in range(thread_count):
            total_thread_count += 1
            proxies_for_web_site.append(
                get_proxy_dict(available_proxy_ports[total_thread_count % len(available_proxy_ports)]))
        proxies.append(tuple(proxies_for_web_site))

    for i in range(0, len(web_site_thread_counts)):
        assert len(proxies[i]) == web_site_thread_counts[i]

    return tuple(proxies)


def get_user_input() -> Tuple[Tuple[int, int, bool], ...]:
    user_input_tuples = []
    for market_id in MARKET_IDS:
        nr_of_threads = int(input(f"[{market_id}] Nr. of threads: "))
        try:
            initial_session_id = int(
                input(f"[{market_id}] Resume session_id [blank makes new]: ")) if nr_of_threads > 0 else None
        except ValueError:
            initial_session_id = None
        start_immediately_str: str = input(
            f"[{market_id}] Start immediately? (True/False)") if nr_of_threads > 0 else "false"
        if start_immediately_str.lower() == "false" or bool(start_immediately_str.lower()) == False:
            start_immediately: bool = False
        else:
            start_immediately: bool = True
        user_input_tuples.append((nr_of_threads, initial_session_id, start_immediately))

    return tuple(user_input_tuples)


def parse_float(unparsed_float: str) -> float:
    return float(re.sub(r'[^\d.]+', '', unparsed_float))


def parse_int(unparsed_int: str) -> int:
    return int(re.sub(r'[^\d]+', '', unparsed_int))


def get_proxy_port(proxy_dict: dict) -> int:
    port = int(proxy_dict["http"].split(":")[-1])
    return port


def get_schemaed_url(unschemaed_url: str, schema: str) -> str:
    return f"{schema}://{unschemaed_url}"


def test_mirror(url: str, headers: dict, proxy: dict, logfunc: Callable[[str], None]) -> bool:
    schemaed_url = get_schemaed_url(url, schema="http")
    for i in range(NR_OF_TRIES_PER_MIRROR):
        try:
            logfunc(f"Try nr. {i+1}, testing {schemaed_url}...")
            requests.get(schemaed_url, headers=headers, proxies=proxy, timeout=MIRROR_TEST_TIMEOUT_LIMIT,
                         allow_redirects=False)
            return True
        except WEB_EXCEPTIONS_TUPLE as e:
            logfunc(f"{type(e).__name__}")
    return False


def do_parameter_sanity_check(proxy_dict_tuples: Tuple[Tuple[Dict], ...], available_ports: List[int],
                              thread_counts: Tuple[int]) -> None:
    from dynamic_config import WEBSITES_TO_BE_SCRAPED
    assert len(proxy_dict_tuples) == len(WEBSITES_TO_BE_SCRAPED)
    for proxy_dicts, thread_count, (market_id, _, _) in zip(proxy_dict_tuples, thread_counts, WEBSITES_TO_BE_SCRAPED):
        if thread_count > len(available_ports) * MAX_MARKET_THREADS_PER_PROXY:
            print(
                f"{market_id} has {thread_count} threads and needs {thread_count*MAX_MARKET_THREADS_PER_PROXY} "
                f"proxies, but only has {len(available_ports)}. Exiting... ")
            exit()
    print("Sanity check complete.")


def get_response_text(response: requests.Response) -> str:
    if response.headers.get('content-encoding') == 'br':
        return brotli.decompress(response.content)
    else:
        return response.text


def get_standardized_listing_type(non_standardized_listing_type: str) -> str:
    conversion_dict: Dict[str, ListingType] = {
        'Physical Listing': ListingType.PHYSICAL,
        'Digital Listing (Manual Fulfillment)': ListingType.MANUAL_DIGITAL,
        'Digital Autoshop Listing': ListingType.AUTO_DIGITAL,
        'Physical Package': ListingType.PHYSICAL,
        'Digital': ListingType.MANUAL_DIGITAL
    }

    return conversion_dict[non_standardized_listing_type].name


def parse_unit_amount_and_unit_type_from_string(time_string: str) -> Tuple[float, str]:
    unit_amount_and_unit_type = time_string.split()
    if len(unit_amount_and_unit_type) == 2:
        unparsed_unit_amount, unit_type = unit_amount_and_unit_type
    elif len(unit_amount_and_unit_type) == 1:
        return 1.0, unit_amount_and_unit_type[0]
    else:
        raise AssertionError(f"Could not parse time unit and time amount in {unit_amount_and_unit_type}")

    if unparsed_unit_amount.find(".") != -1:
        # the unit amount seems to be a float
        unit_amount: float = float(unparsed_unit_amount)
    else:
        # assuming the unit amount is an integer
        unit_amount = float(text2digits.Text2Digits().convert_to_digits(str(unparsed_unit_amount)))

    return unit_amount, unit_type


def parse_time_delta_from_string(time_string: str) -> timedelta:
    unit_amount, unit_type = parse_unit_amount_and_unit_type_from_string(time_string)

    if unit_type[:3] == "day":
        return timedelta(seconds=unit_amount * ONE_DAY)
    elif unit_type[:4] == "week":
        return timedelta(seconds=unit_amount * ONE_WEEK)
    elif unit_type == "hours":
        return timedelta(seconds=unit_amount * ONE_HOUR)
    else:
        raise AssertionError(f'Unknown unit type {unit_type}')


COUNTRY_NAME_SPLIT_REGEX = re.compile(r"\s|\(.*\)")


def determine_real_country(country_name: str) -> Tuple[str, Optional[str], Optional[str], bool]:
    # returns country_name, iso_alpha2_code, iso_alpha3_code, is_continent
    country_name = country_name.strip()
    if country_name in CONTINENT_DICTIONARY.keys():
        return CONTINENT_DICTIONARY[country_name], None, None, True
    else:
        if country_name in COUNTRY_DICT.keys():
            country_name = COUNTRY_DICT[country_name]
        name_components = re.split(COUNTRY_NAME_SPLIT_REGEX, country_name)
        while len(name_components) > 0:
            try:
                country_result = pycountry.countries.search_fuzzy(" ".join(name_components))[0]
                return country_result.name, country_result.alpha_2, country_result.alpha_3, False
            except LookupError:
                # if we found no countries, we cut out a word from the country name and try again
                name_components = name_components[:-1]

        return country_name, None, None, False


def get_estimated_finish_time_as_readable_string(start_time: float, initial_queue_size: int, queue_size: int) -> str:
    pages_left = queue_size
    pages_scraped = initial_queue_size - queue_size
    time_spent = time() - start_time
    time_left = (pages_left / pages_scraped) * time_spent

    days = time_left // 86400
    hours = (time_left - days * 86400) // 3600
    minutes = (time_left - days * 86400 - hours * 3600) // 60
    seconds = time_left - days * 86400 - hours * 3600 - minutes * 60
    result: str = ("{0} day{1}, ".format(days, "s" if days != 1 else "") if days else "") + \
                  ("{0} hour{1}, ".format(hours, "s" if hours != 1 else "") if hours else "") + \
                  ("{0} minute{1}, ".format(minutes, "s" if minutes != 1 else "") if minutes else "") + \
                  ("{0} second{1}, ".format(seconds, "s" if seconds != 1 else "") if seconds else "")
    return result
