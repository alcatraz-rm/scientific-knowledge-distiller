import csv
import itertools
import os.path
import subprocess
from copy import deepcopy
from itertools import chain
from pprint import pprint
from typing import Iterable, Dict

from search_engine.databases.database_client import SearchResult
from utils.publications_graph import PublicationsGraph


class Deduplicator:
    def __init__(self):
        initial_wd = os.getcwd()

        while os.path.split(os.getcwd())[-1] != 'scientific-knowledge-distiller':
            os.chdir(os.path.join(os.getcwd(), '..'))

        self._root_path = os.getcwd()
        self._path_to_deduplication_script = os.path.join(self._root_path, 'deduplication', 'deduplicate.r')
        os.chdir(initial_wd)

    def deduplicate(self, *iterables) -> Iterable[SearchResult]:
        publications_dict = {pub.id: pub for pub in chain(*iterables)}
        print(f'total found: {len(publications_dict)}')

        pubs_graph = PublicationsGraph()
        for pub_id in publications_dict:
            pubs_graph.add_vertex(pub_id)

        self._dump_to_csv(publications_dict)
        self.__run_deduplication_script()

        path_to_deduplication_module = os.path.join(self._root_path, 'deduplication')
        possible_duplicates_path = os.path.join(path_to_deduplication_module, '_manual_dedup.csv')

        false_positive = 0
        true_positive = 0
        false_negative = 0
        true_negative = 0

        with open(possible_duplicates_path, 'r', encoding='utf-8') as manual_dedup_csv:
            manual_dedup_csv.readline()
            reader = csv.DictReader(manual_dedup_csv,
                                    fieldnames=['id1', 'id2', 'author1', 'author2', 'author', 'title1', 'title2',
                                                'title', 'abstract1', 'abstract2', 'abstract', 'year1', 'year2', 'year',
                                                'number1', 'number2', 'number', 'pages1', 'pages2', 'pages', 'volume1',
                                                'volume2', 'volume', 'journal1', 'journal2', 'journal', 'isbn', 'isbn1',
                                                'isbn2', 'doi1', 'doi2', 'doi', 'record_id1', 'record_id2', 'label1',
                                                'label2', 'source1', 'source2'
                                                ]
                                    )

            rows = []
            for row in reader:
                rows.append(deepcopy(row))

            for n, row in enumerate(rows):
                id_1, id_2 = row['record_id1'].lower(), row['record_id2'].lower()
                are_duplicates = Deduplicator.are_duplicates(row)
                if are_duplicates:
                    pubs_graph.add_edge(id_1, id_2)

                if row['doi'] != 'NA':
                    if row['doi'] == '1' and are_duplicates:
                        true_positive += 1
                        continue
                    if row['doi'] != '1' and not are_duplicates:
                        true_negative += 1
                        continue

                print(f"{n}/{len(rows)}\ntitle 1: {row['title1']}\n"
                      f"title 2: {row['title2']}\n"
                      f"title sim: {row['title']}\n\n"
                      f"author 1: {row['author1']}\n"
                      f"author 2: {row['author2']}\n"
                      f"author sim: {row['author']}\n\n"
                      f"abstract 1: {row['abstract1']}\n\n"
                      f"abstract 2: {row['abstract2']}\n\n"
                      f"abstract sim: {row['abstract']}\n\n"
                      f"doi 1: {row['doi1']}\n"
                      f"doi 2: {row['doi2']}\n"
                      f"doi sim: {row['doi']}\n\n"
                      f"year 1: {row['year1']}\n"
                      f"year 2: {row['year2']}\n\n"
                      f"source 1: {row['source1']}\n"
                      f"source 2: {row['source2']}\n"
                      )
                print(f'system decision: {"DUPLICATES" if are_duplicates else "NOT DUPLICATES"}')
                mark = input('mark: ').strip()

                if mark == '0' and are_duplicates:
                    false_positive += 1
                if mark == '0' and not are_duplicates:
                    false_negative += 1

                if are_duplicates and mark != '0':
                    true_positive += 1
                if not are_duplicates and mark != '0':
                    true_negative += 1

            print('TP:', true_positive)
            print('FP:', false_positive)
            print('TN:', true_negative)
            print('FN:', false_negative)

        connected_components = pubs_graph.connected_components()

        unique_pubs_ids = set()
        for component in connected_components:
            base_pub = self._merge_publications(*[publications_dict[pub_id] for pub_id in component])
            component.discard(base_pub.id)

            publications_dict[base_pub.id] = deepcopy(base_pub)
            unique_pubs_ids.add(base_pub.id)

        unique_cites_path = os.path.join(path_to_deduplication_module, '_unique_citations.csv')
        os.remove(unique_cites_path)
        os.remove(possible_duplicates_path)
        os.remove(os.path.join(path_to_deduplication_module, '_dump_tmp.csv'))

        for pub_id in unique_pubs_ids:
            yield publications_dict[pub_id]

    def _merge_publications(self, *pubs) -> SearchResult:
        if len(pubs) == 1:
            return pubs[0]

        base_pub = self._choose_best(*pubs)

        for p in pubs:
            if p.id != base_pub.id:
                base_pub.add_version(p)

        return base_pub

    @staticmethod
    def _choose_best(*pubs) -> SearchResult:
        return min(*pubs, key=lambda x: x.empty_fields)

    # NOTE: HERE we perform manual deduplication
    @staticmethod
    def are_duplicates(row):
        doi = -1
        if row['doi'] != 'NA':
            doi = float(row['doi'])

        if doi == 1 and row['doi1']:
            return True
        if doi < 1 and doi != -1:
            return False

        if float(row['author']) >= 0.6 and row['title'] == '1':
            return True
        if row['title'] == '1' and row['abstract'] == '1' and row['year'] == '1':
            return True
        if float(row['author']) >= 0.5 and row['title'] == '1' and row['abstract'] == '1':
            return True

        return False

    def _dump_to_csv(self, publications: Dict[int, SearchResult]):
        # TODO: add env variable for path to deduplication raw dump

        path_to_dump = os.path.join(self._root_path, 'deduplication', '_dump_tmp.csv')

        with open(path_to_dump, 'w', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=SearchResult.csv_keys())
            writer.writeheader()

            for pub_id in publications:
                writer.writerow(publications[pub_id].to_csv())

    def __run_deduplication_script(self):
        print('starting deduplication...')
        p = subprocess.run(['Rscript', self._path_to_deduplication_script], capture_output=True, text=True,
                           cwd=os.path.join(self._root_path, 'deduplication'))
        p.check_returncode()
