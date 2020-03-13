import pickle
import re
from datetime import datetime
from shutil import copyfile
from typing import Dict


def get_metadata_dict(file_path: str) -> Dict:
    path_parts = file_path.split("/")
    matches: int = 0
    for part in path_parts:
        match = re.search(r"201[45]-[0-1][0-9]-[0-3][0-9]", part)
        if match:
            matches += 1
            date_str = part[:10]

    if file_path != "/home/magnus/Documents/temp/gwern_dream/dreammarket/./gwern_file_list.txt":
        assert matches == 1
        # noinspection PyUnboundLocalVariable
        year, month, day = [int(i) for i in date_str.split("-")]
        url = "/" + path_parts[-1]
        meta_data_dict = {
            "meta": {
                "received_on": datetime(year=year, month=month, day=day)
            },
            "url": url
        }
        return meta_data_dict

dir_path = "/home/magnus/Documents/temp/gwern_dream/dreammarket"
out_path = "/home/magnus/Documents/dream_market/parsed_html2"
file_with_list_of_files = "/home/magnus/Documents/temp/gwern_dream/dreammarket/gwern_file_list.txt"
with open(file_with_list_of_files, "r") as f:
    files = [s.strip() for s in f.readlines()]

for i, relative_file_path in enumerate(files):
    file_path = f"{dir_path}/{relative_file_path}"

    file_name = relative_file_path.split("/")[-1]
    output_file_path = f"{out_path}/{file_name}.html"
    output_file_path_metadata = f"{out_path}/{file_name}.meta"

    meta_data_dict: Dict = get_metadata_dict(file_path)
    if meta_data_dict:
        copyfile(file_path, output_file_path)

        with open(output_file_path_metadata, "wb") as output:
            # '2018-05-25 09:19:18'
            # date_time_str = '2018-06-29 08:15:27.243860'
            # date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
            pickle.dump(meta_data_dict, output)

        if i % 1000 == 0:
            print(f"{i}/{len(files)}")
