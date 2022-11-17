import json
from pprint import pprint

with open('papers_info.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

for row in data:
    print(row)

    input('paste title to a.txt and press enter')
    with open('a.txt', 'r', encoding='utf-8') as txt:
        title = txt.read()
    data[row]['title'] = title

    input('paste abstract to t.txt and press enter')

    with open('t.txt', 'r', encoding='utf-8') as txt:
        abstract = txt.read()
    data[row]['abstract'] = abstract


with open('papers_data.json', 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=4)
