from datetime import datetime
import inspect
import time

import requests
from urllib3.exceptions import HTTPError


class BadGatewayException(HTTPError):
    pass


class InternalServerErrorException(HTTPError):
    pass

def pretty_print_GET(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    return '{}\n{}\r\n{}\r\n\r'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items())
    )


def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    return '{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    )


def error_is_sqlalchemy_error(error_string):
    return error_string.find("site-packages/sqlalchemy") != -1 \
           or error_string.find("\'NoneType\' object has no attribute \'have_result_set\'") != -1 \
           or error_string.find("MySQL") != -1


def print_error_to_file(thread_id, error_string):
    file_name = "thread_" + str(thread_id) + "_error"
    file = open(file_name, "w")
    file.write(error_string)
    file.close()


def get_error_string(scraping_object, error_traceback, sys_exec_info):
    time_of_error = str(datetime.fromtimestamp(time.time()))
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


def is_bad_gateway(response: requests.Response):
    if response.status_code == 502:
        return True

    for history_response in response.history:
        if history_response.status_code == 502:
            return True

    return False


def is_internal_server_error(response : requests.Response):
    if response.status_code == 500:
        return True

    for history_response in response.history:
        if history_response.status_code == 500:
            return True

    return False
