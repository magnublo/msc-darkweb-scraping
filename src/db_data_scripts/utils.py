import os
import re
from datetime import datetime
from typing import List, Tuple

import numpy

from definitions import ROOT_SRC_DIR
from environment_settings import DB_NAME, DB_HOST


def get_most_recent_file_from_suffix(suffix: str) -> str:
    regex = r".+__.+__([0-3][0-9]-[0-1][0-9]-[0-9]{4}(?:-[0-9]{2}-[0-9]{2}-[0-9]{2})?)__" + suffix + "\.pickle"

    dir_path = f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data"
    files = os.listdir(dir_path)

    files_and_dates: List[Tuple[str, datetime]] = []

    for file in files:
        match = re.match(regex, file)
        if match:
            start_index = match.regs[1][0]
            end_index = match.regs[1][1]
            date_str = file[start_index:end_index]
            day, month, year, hour, minute, second = ([int(i) for i in date_str.split("-")] + [0] * 3)[:6]
            files_and_dates.append((file, datetime(day=day, month=month, year=year)))
            files_and_dates.sort(key=lambda fd: fd[1])
    most_recent_listing_dump_file = files_and_dates[-1][0]
    return f"{dir_path}/{most_recent_listing_dump_file}"


def get_most_recent_listing_observation_category_dump_file_path() -> str:
    return get_most_recent_file_from_suffix("all_listing_observation_category")


def get_most_recent_listing_dump_file_path() -> str:
    return get_most_recent_file_from_suffix("all_listings")


def get_most_recent_feedback_dump_file_path() -> str:
    return get_most_recent_file_from_suffix("all_feedbacks")


def generate_output_file_name(suffix: str, entries: Tuple) -> str:
    last_hundred_entries = entries[-100:]
    average_timestamp = numpy.average([e.created_date.timestamp() for e in last_hundred_entries])
    exact_date = datetime.utcfromtimestamp(average_timestamp)
    date_str = f"{str(exact_date.day).zfill(2)}-{str(exact_date.month).zfill(2)}-{str(exact_date.year).zfill(2)}-{str(exact_date.hour).zfill(2)}-{str(exact_date.minute).zfill(2)}-{str(exact_date.second).zfill(2)}"
    return f"{ROOT_SRC_DIR}/db_data_scripts/pickle_data/{DB_HOST}__{DB_NAME}__{date_str}__{suffix}.pickle"
