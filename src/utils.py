import inspect
import re
from datetime import datetime, timedelta
from time import time, sleep
from typing import Tuple, List

import requests
from bs4 import BeautifulSoup
from regex.regex import Match
from urllib3.exceptions import HTTPError

from definitions import BEAUTIFUL_SOUP_HTML_PARSER, MARKET_IDS
from environment_settings import DEBUG_MODE
from src.tor_proxy_check import get_proxy_dict


class LoggedOutException(Exception):
    DEFAULT_TEXT = "Cookie appears to have been invalidated by remote website."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class BadGatewayException(HTTPError):
    DEFAULT_TEXT = "Received response code 502."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class InternalServerErrorException(HTTPError):
    DEFAULT_TEXT = "Received response code 500."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class GenericException(BaseException):
    DEFAULT_TEXT = "Generic exception."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


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


def print_error_to_file(thread_id, error_string, file_postfix=None) -> None:
    file_name = f"thread_{thread_id}_error"
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


def is_bad_gateway(response: requests.Response) -> bool:
    if response.status_code == 502:
        return True

    for history_response in response.history:
        if history_response.status_code == 502:
            return True

    return False


def is_internal_server_error(response: requests.Response) -> bool:
    if response.status_code == 500:
        return True

    for history_response in response.history:
        if history_response.status_code == 500:
            return True

    return False


def queue_is_empty(queue) -> bool:
    is_empty = queue.empty()
    sleep(100)  # Must be sure that queue is indeed empty.
    return queue.empty() and is_empty


# TODO: Rework method. Let it accept str, not requests.Response. Implement integration tests so that
# TODO: self.get_logged_in_web_response is mocked with a method that returns file content based on url argument.
# TODO: Remove working_dir argument. Let method be proxied by BaseScraper method which passes working_dir.
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
        start_immediately = bool(input(f"[{market_id}] Start immediately? (True/False)")) if nr_of_threads > 0 else True
        user_input_tuples.append((nr_of_threads, initial_session_id, start_immediately))

    return tuple(user_input_tuples)


def _parse_float(unparsed_float: str) -> float:
    return float(re.sub(r'[^\d.]+', '', unparsed_float))


def _parse_int(unparsed_float: str) -> int:
    return int(re.sub(r'[^\d.]+', '', unparsed_float))