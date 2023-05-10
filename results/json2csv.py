import csv
import json
import os

print(os.listdir('.'))

files = os.listdir('.')
for file in files:
    if file.endswith('json'):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data_csv = []

        for row in data:
            row_dict = {'authors': ','.join(row['authors']), 'title': row['title'],
                        'pub_date': row['publication_date'], 'source': row['source'],
                        'doi': row['doi'], 'abstract': row['abstract'], 'rank': row['rank'], 'url': '\n'.join(row['urls'])}
            data_csv.append(row_dict)

        with open(file.replace('json', 'csv'), 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, data_csv[0].keys())
            writer.writeheader()
            writer.writerows(data_csv)
