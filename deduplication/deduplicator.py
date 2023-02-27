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
        unique_cites_path = os.path.join(path_to_deduplication_module, '_unique_citations.csv')
        possible_duplicates_path = os.path.join(path_to_deduplication_module, '_manual_dedup.csv')

        # TODO: do something with unique citations file
        with open(unique_cites_path, 'r', encoding='utf-8') as unique_pubs_csv:
            reader = csv.DictReader(unique_pubs_csv,
                                    fieldnames=['duplicate_id', 'record_id', 'author', 'year', 'journal', 'doi',
                                                'title', 'pages', 'volume', 'number', 'abstract', 'isbn', 'label',
                                                'source'
                                                ])
            unique_pubs_ids = {row['record_id'].lower() for row in reader}

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

            for row in reader:
                id_1, id_2 = row['record_id1'].lower(), row['record_id2'].lower()
                if Deduplicator.are_duplicates(row):
                    # pprint(row)  # TODO
                    # input()
                    # best_id = Deduplicator._choose_best(publications_dict[id_1],
                    #                                     publications_dict[id_2])
                    # unique_pubs_ids.add(best_id)
                    # unique_pubs_ids.discard(id_2 if best_id == id_1 else id_1)

                    pubs_graph.add_edge(id_1, id_2)
                # else:
                #     unique_pubs_ids.add(id_1)
                #     unique_pubs_ids.add(id_2)

        connected_components = pubs_graph.connected_components()

        unique_pubs_ids = set()
        for component in connected_components:
            base_pub = self._merge_publications(*[publications_dict[pub_id] for pub_id in component])
            component.discard(base_pub.id)

            publications_dict[base_pub.id] = deepcopy(base_pub)
            unique_pubs_ids.add(base_pub.id)

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
        return max(*pubs, key=lambda x: x.empty_fields)

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
        if row['author'] == '1' and row['title'] == '1' and row['abstract'] == '1': # useless
            return True

        if row['title'] == '1':
            pass

        if row['year1'] != row['year2'] and \
                row['year1'] and \
                row['year2'] and \
                len(row['year1']) == 4 and \
                len(row['year2']) == 4:
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
