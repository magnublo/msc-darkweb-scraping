import base64
import json
import os
import pickle
import re
from datetime import datetime

dir_path = "/home/magnus/PycharmProjects/msc/src/dream/scraped_html"
out_path = "/home/magnus/PycharmProjects/msc/src/dream/parsed_html"
files = os.listdir(dir_path)





for i, file in enumerate([f for f in files if re.match(r"[0-9]{13}_[0-9]{4}_[a-z0-9]{40}", f)]):
    file_path = f"{dir_path}/{file}"
    output_file_path = f"{out_path}/{file}"

    with open(file_path, "r") as f:
        file_content = f.read()
        file_json = json.loads(file_content)

    base64_body = file_json["body"] + "========"
    byte_body = base64.b64decode(base64_body)

    with open(f"{output_file_path}.html", "wb") as output:
        output.write(byte_body)

    with open(f"{output_file_path}.meta", "wb") as output:
        # '2018-05-25 09:19:18'
        # date_time_str = '2018-06-29 08:15:27.243860'
        # date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
        file_json["meta"]["received_on"] = datetime.strptime(file_json["meta"]["received_on"], '%Y-%m-%d %H:%M:%S')
        del file_json["body"]
        pickle.dump(file_json, output)

    if i % 1000 == 0:
        print(f"{i}/{len(files)}")
