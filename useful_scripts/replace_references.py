import os
import re

dir_path = "/home/magnus/Documents/dream_market/parsed_html"
files = os.listdir(dir_path)
file_refs = set()
valid_files = [f for f in files if re.match(r"[0-9]{13}_[0-9]{4}_[a-z0-9]{40}\.html", f)]
for i, file in enumerate(valid_files):
    k = 0
    match = None
    file_path = f"{dir_path}/{file}"

    with open(file_path, "rb") as f:
        file_content_bytes = f.read()

    try:
        file_content = file_content_bytes.decode("unicode_escape")
    except UnicodeDecodeError:
        file_content = None

    if file_content:
        pos = 0
        while k == 0 or match is not None:
            match = re.search(r"(?:(?:src|href)=)\"([a-z0-9.\-\_\/]+\.[a-z0-9]{2,4})\"", file_content[pos:])
            if match:
                k += 1
                start_index = match.regs[1][0] + pos
                pos = end_index = match.regs[1][1] + pos
                file_ref = file_content[start_index:end_index]
                file_refs.add(file_ref)
                new_file_ref = "./../" + file_ref.split("/")[-1]
                file_content = file_content[:start_index] + new_file_ref + file_content[end_index:]
            else:
                break

        if k > 0:
            output_file_path = f"{dir_path}/../new_refs_parsed_html/{file}"
            with open(output_file_path, "w") as f:
                f.write(file_content)

        if i % 1000 == 0:
            print(f"{i}/{len(files)}")

print("\n".join(file_refs))
