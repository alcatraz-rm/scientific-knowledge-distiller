import csv
import itertools
import os.path
import subprocess
from itertools import chain
from typing import Iterable, Dict

from search_engine.databases.database import SearchResult


class Deduplicator:
    def __init__(self):
        self._path_to_deduplication_script = os.path.join(os.getcwd(), 'deduplication', 'deduplicate.r')

    def deduplicate(self, *iterables):
        publications_dict = {pub.id: pub for pub in chain(*iterables)}

        Deduplicator._dump_to_csv(publications_dict)
        self.__run_deduplication_script()
        unique_pubs_ids = set()

        path_to_deduplication_module = os.path.join(os.getcwd(), 'deduplication')
        with open(os.path.join(path_to_deduplication_module, '_unique_citations.csv'), 'r',
                  encoding='utf-8') as unique_pubs_csv:
            reader = csv.DictReader(unique_pubs_csv,
                                    fieldnames=['duplicate_id', 'record_id', 'author', 'year', 'journal', 'doi',
                                                'title', 'pages', 'volume', 'number', 'abstract', 'isbn', 'label',
                                                'source'
                                                ])
            unique_pubs_ids = {row['record_id'].lower() for row in reader}

        with open(os.path.join(path_to_deduplication_module, '_manual_dedup.csv'), 'r',
                  encoding='utf-8') as manual_dedup_csv:
            manual_dedup_csv.readline()
            reader = csv.DictReader(manual_dedup_csv,
                                    fieldnames=['id1', 'id2', 'author1', 'author2', 'author', 'title1', 'title2',
                                                'title', 'abstract1', 'abstract2', 'abstract', 'year1', 'year2', 'year',
                                                'number1', 'number2', 'number', 'pages1', 'pages2', 'pages', 'volume1',
                                                'volume2', 'volume', 'journal1', 'journal2', 'journal', 'isbn', 'isbn1',
                                                'isbn2', 'doi1', 'doi2', 'doi', 'record_id1', 'record_id2', 'label1',
                                                'label2', 'source1', 'source2'
                                                ])
            # NOTE: HERE we perform manual deduplication
            for row in reader:
                id_1 = row['record_id1'].lower()
                id_2 = row['record_id2'].lower()
                if row['doi1'] == row['doi2'] and row['doi1']:
                    best_id = Deduplicator.choose_best(publications_dict[id_1],
                                                       publications_dict[id_2])
                    unique_pubs_ids.add(best_id)
                    unique_pubs_ids.discard(id_2 if best_id == id_1 else id_1)
                else:
                    unique_pubs_ids.add(id_1)
                    unique_pubs_ids.add(id_2)

        for publication in publications_dict.values():
            if publication.id in unique_pubs_ids:
                yield publication

    @staticmethod
    def choose_best(pub1: SearchResult, pub2: SearchResult) -> str:
        if pub1.empty_fields <= pub2.empty_fields:
            return pub1.id
        return pub2.id

    @staticmethod
    def _dump_to_csv(publications: Dict[int, SearchResult]):
        # TODO: add env variable for path to deduplication raw dump
        path_to_dump = os.path.join(os.getcwd(), 'deduplication', '_dump_tmp.csv')

        with open(path_to_dump, 'w', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=SearchResult.csv_keys())
            writer.writeheader()

            for pub_id in publications:
                writer.writerow(publications[pub_id].to_csv())

    def __run_deduplication_script(self):
        p = subprocess.run(['Rscript', self._path_to_deduplication_script], capture_output=True, text=True,
                           cwd=os.path.join(os.getcwd(), 'deduplication'))
        p.check_returncode()