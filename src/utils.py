import inspect
from datetime import datetime
from time import time, sleep

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import HTTPError

from definitions import BEAUTIFUL_SOUP_HTML_PARSER
from environment_settings import DEBUG_MODE



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


def get_page_as_soup_html(working_dir, web_response, file_name=None, use_offline_file=DEBUG_MODE) -> BeautifulSoup:
    if use_offline_file:
        file_name = open(working_dir + file_name, "r")
        soup_html = BeautifulSoup(file_name, features=BEAUTIFUL_SOUP_HTML_PARSER)
        file_name.close()
        return soup_html
    else:
        return BeautifulSoup(web_response.text, features=BEAUTIFUL_SOUP_HTML_PARSER)


def get_logger_name(cls: object):
    return cls.__name__