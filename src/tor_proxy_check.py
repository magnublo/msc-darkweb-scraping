import math
from enum import Enum
from multiprocessing import Queue
from threading import RLock, Thread
from typing import Tuple, List

import requests
from blessings import Terminal
from requests import RequestException
from sty import fg
from tabulate import tabulate

from definitions import TOR_PROJECT_URL_FOR_CONFIGURATION_CHECK, TOR_PROJECT_CORRECT_CONFIGURATION_SUCCESS_MESSAGE, \
    RECOMMENDED_NR_OF_THREADS_PER_TOR_PROXY
from environment_settings import LOWEST_TOR_PORT, TOR_PROXY_SERVER_ADDRESS

TERMINAL = Terminal()

TABLE_FORMAT = "plain"
CHECK_MARK = u'\u2714'
X_MARK = u'\u2718'
CLOCK = u'\u29d6'

WAITING_STRING = f"Waiting {TERMINAL.blink(CLOCK)}"
ERROR_STRING = f"Error {X_MARK}"
OK_STRING = f"OK {CHECK_MARK}"

LONGEST_STRING = max([WAITING_STRING, ERROR_STRING, OK_STRING], key=lambda s: len(s.encode("utf-8")))
COLALIGN = ("left", "left")
TABLE_HEADERS = [f"{TERMINAL.bold('PROXY HOST ADDRESS')}", f"\t {TERMINAL.bold('STATUS')}"]


class ProxyStatus(Enum):
    ERROR = 0,
    OK = 1,
    WAITING = 2


def format_str(color_code: str, string: str) -> str:
    return f"{color_code}{string}{fg.rs}"


def get_status_row_tuple(proxy_state: ProxyStatus, port: int) -> Tuple[str, str]:
    address_column = f"{TERMINAL.clear_eol}{TOR_PROXY_SERVER_ADDRESS}:{port}"

    if proxy_state == ProxyStatus.WAITING:
        status_column = format_str(fg.yellow, WAITING_STRING)
    elif proxy_state == ProxyStatus.ERROR:
        status_column = format_str(fg.red, ERROR_STRING)
    elif proxy_state == ProxyStatus.OK:
        status_column = format_str(fg.blue, OK_STRING)
    else:
        raise Exception

    return address_column, status_column


def print_tor_proxy_statuses(statuses: List[Tuple[ProxyStatus, int]]):
    print('')
    output_lines = []
    for proxy_status, port in statuses:
        output_lines.append(get_status_row_tuple(proxy_status, port))
    print(tabulate([output_line for output_line in output_lines], headers=TABLE_HEADERS,
                   tablefmt=TABLE_FORMAT, colalign=COLALIGN))


def get_proxy_dict(port: int) -> dict:
    HTTP_PROTOCOLS = ["http", "https"]
    proxy_dict = {}
    for protocol in HTTP_PROTOCOLS:
        proxy_dict[protocol] = f"socks5h://{TOR_PROXY_SERVER_ADDRESS}:{port}"
    return proxy_dict


def print_tor_proxy_status(proxy_status: ProxyStatus, proxy_port: int, line_nr: int, lock: RLock, total_lines: int):
    row_tuple = get_status_row_tuple(proxy_status, proxy_port)
    row_str = str(tabulate([row_tuple], headers=TABLE_HEADERS, tablefmt=TABLE_FORMAT, colalign=COLALIGN)).split('\n')[1]
    line_offset = total_lines - line_nr
    lock.acquire()
    print(f"{TERMINAL.move_up*(line_offset)}{row_str}{TERMINAL.move_down*(line_offset-1)}")
    lock.release()


def check_proxy(line_nr: int, proxy_port: int, lock: RLock, total_lines: int, result_queue: Queue) -> None:
    proxy = get_proxy_dict(proxy_port)
    res_text = ""
    for _ in range(5):
        try:
            res_text = requests.get(TOR_PROJECT_URL_FOR_CONFIGURATION_CHECK, proxies=proxy).text
            break
        except RequestException:
            pass
    proxy_works = res_text.find(TOR_PROJECT_CORRECT_CONFIGURATION_SUCCESS_MESSAGE) != -1
    proxy_status = ProxyStatus.OK if proxy_works else ProxyStatus.ERROR
    print_tor_proxy_status(proxy_status, proxy_port, line_nr, lock, total_lines)
    result_queue.put((proxy_port, proxy_status.value))

def get_recommended_nr_of_tor_proxies(total_nr_of_threads: int) -> int:
    return math.ceil(total_nr_of_threads / RECOMMENDED_NR_OF_THREADS_PER_TOR_PROXY)

def get_available_tor_proxies(total_nr_of_threads: int) -> List[int]:
    recommended_nr_of_tor_proxies = get_recommended_nr_of_tor_proxies(total_nr_of_threads)
    statuses = []
    threads = []
    result_queue = Queue()
    lock = RLock()
    port_sequence = [i for i in range(LOWEST_TOR_PORT, LOWEST_TOR_PORT + recommended_nr_of_tor_proxies * 2, 2)]

    for port in port_sequence:
        statuses.append((ProxyStatus.WAITING, port))

    print_tor_proxy_statuses(statuses)

    for line_nr, port in zip(range(len(port_sequence)), port_sequence):
        t = Thread(target=check_proxy, args=(line_nr, port, lock, len(port_sequence), result_queue))
        threads.append(t)
        t.start()

    [t.join() for t in threads]
    proxies = [result_queue.get() for _ in threads]

    print('')
    nr_of_working_proxies = sum([proxy[1] == ProxyStatus.OK for proxy in proxies])
    if nr_of_working_proxies < recommended_nr_of_tor_proxies:
        print(f"{fg.yellow}WARNING. Your Tor proxy host '{TOR_PROXY_SERVER_ADDRESS}' only has {nr_of_working_proxies} working proxies, against recommended {recommended_nr_of_tor_proxies}.")
        print(f"{fg.yellow}Run script on {TOR_PROXY_SERVER_ADDRESS} to fix.")

    return [proxy[0] for proxy in proxies]