import csv
import json
import os

p = '6'
print(os.listdir(p))
files = os.listdir(p)
for file in files:
    if file.endswith('json'):
        with open(os.path.join(p, file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        data_csv = []

        for row in data:
            row_dict = {'authors': ','.join(row['authors']), 'title': row['title'],
                        'pub_date': row['publication_date'], 'source': row['source'],
                        'doi': row['doi'], 'abstract': row['abstract'], 'rank': row['rank'], 'url': '\n'.join(row['urls'])}
            data_csv.append(row_dict)

        with open(os.path.join(p, file.replace('json', 'csv')), 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, data_csv[0].keys())
            writer.writeheader()
            writer.writerows(data_csv)
