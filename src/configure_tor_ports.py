import errno
import os
import socket
import sys
from multiprocessing import Queue
from threading import Thread, Lock
from typing import List, Tuple

from tabulate import tabulate

from environment_settings import LOWEST_TOR_PORT
from src.tor_proxy_check import get_recommended_nr_of_tor_proxies, ProxyStatus as PortStatus, get_status_row_tuple, \
    TABLE_FORMAT, COLALIGN, TABLE_HEADERS, TERMINAL

RANDOM_STRING_1 = "NSwxBq3JH4AENuqMzJ2PM7uSnHuYHtyra2"
RANDOM_STRING_2 = "yEkrgqzs7kFnjSyn6RR8jUscpKD2FrNUuz"

def run_as_root_or_exit() -> None:
    try:
        os.rename(f'/etc/{RANDOM_STRING_1}', f'/etc/{RANDOM_STRING_2}')
        os.rename(f'/etc/{RANDOM_STRING_2}', f'/etc/{RANDOM_STRING_1}')
    except IOError as e:
        if e.errno == errno.EPERM or e.errno == errno.ENOENT:
           print("This script needs to be run with root privileges.")
           sys.exit(1)


def print_port_status(proxy_status: PortStatus, proxy_port: int, line_nr: int, lock: Lock, total_lines: int):
    row_tuple = get_status_row_tuple(proxy_status, proxy_port)
    row_str = str(tabulate([row_tuple], headers=TABLE_HEADERS, tablefmt=TABLE_FORMAT, colalign=COLALIGN)).split('\n')[1]
    line_offset = (total_lines - line_nr)
    with lock:
        print(f"{TERMINAL.move_up*(line_offset)}{row_str}{TERMINAL.move_down*(line_offset-1)}")


def print_port_statuses(statuses: List[Tuple[PortStatus, int]]):
    print('')
    output_lines = []
    for proxy_status, port in statuses:
        output_lines.append(get_status_row_tuple(proxy_status, port))
    print(tabulate([output_line for output_line in output_lines], headers=TABLE_HEADERS,
                   tablefmt=TABLE_FORMAT, colalign=COLALIGN))


def check_port(line_nr: int, port: int, lock: Lock, total_nr_of_lines: int, result_queue: Queue) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(('127.0.0.1', port))
    port_is_busy = result == 0
    s.close()
    port_status = PortStatus.ERROR if port_is_busy else PortStatus.OK
    print_port_status(port_status, port, line_nr, lock, total_nr_of_lines)
    result_queue.put((port, port_status))


def get_busy_ports(socks_ports: List[int], control_ports: List[int]) -> List[int]:
    all_ports = socks_ports + control_ports
    all_ports.sort()
    statuses = []
    lock = Lock()
    result_queue = Queue()
    threads = []

    for port in all_ports:
        statuses.append((PortStatus.WAITING, port))

    print_port_statuses(statuses)

    for line_nr, port in zip(range(len(all_ports)), all_ports):
        t = Thread(target=check_port, args=(line_nr, port, lock, len(all_ports), result_queue))
        threads.append(t)
        t.start()

    [t.join() for t in threads]
    ports = [result_queue.get() for _ in threads]

    print('')

    return [port[0] for port in ports if port[1] == PortStatus.ERROR]

# nr_of_threads = int(input("Number of scraping threads this Tor service should be configured to accomodate: "))
# os.subprocess.call(["sudo", "service", "tor", "stop"])
# recommended_nr_of_tor_proxies = get_recommended_nr_of_tor_proxies(nr_of_threads)
# socks_port_sequence = [i for i in range(LOWEST_TOR_PORT, LOWEST_TOR_PORT + recommended_nr_of_tor_proxies * 2, 2)]
# control_port_sequence = [i for i in range(LOWEST_TOR_PORT+1, LOWEST_TOR_PORT + recommended_nr_of_tor_proxies * 2 + 1, 2)]
# busy_ports = get_busy_ports(socks_port_sequence, control_port_sequence)

# if len(busy_ports) > 0:
#     pass
#
# for i in range(0, nr_of_threads):
#     conf = f"""SocksPort {9050+i*2}
#     ControlPort {9051+i*2}
#     DataDirectory /var/lib/tor{i}"""
#
#     file = open(f"/etc/tor/torrc{i}", "w")
#     file.write(conf)
#     file.close()
#
#     os.mkdir(f"/var/lib/tor{i}")
#     os.subprocess.call(["tor", "-f", f"/etc/tor/torrc.{i}"])


