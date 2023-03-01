import json
import codecs

with open('dump.json', encoding='utf-8') as file1, codecs.open('new_json.json', 'w', 'utf-8') as file2:
    read_file = file1.read()
    load_file = json.loads(read_file)
    json.dump(load_file, file2, indent=4, ensure_ascii=False)


