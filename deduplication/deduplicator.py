import csv
import json
import os.path
import subprocess
from copy import deepcopy
from itertools import chain
from pprint import pprint
from typing import Iterable, Dict

import pdfkit
from json2html import json2html

from search_engine.databases.database_client import Document
from utils.publications_graph import PublicationsGraph


class Deduplicator:
    def __init__(self):
        initial_wd = os.getcwd()

        while os.path.split(os.getcwd())[-1] != 'scientific-knowledge-distiller':
            os.chdir(os.path.join(os.getcwd(), '..'))

        self._root_path = os.getcwd()
        self._path_to_deduplication_script = os.path.join(self._root_path, 'deduplication', 'deduplicate.r')
        os.chdir(initial_wd)

    def deduplicate(self, remove_without_title=True, *iterables) -> Iterable[Document]:
        publications_dict = {pub.id: pub for pub in chain(*iterables) if
                             (remove_without_title and pub.title) or not remove_without_title}
        print(f'total found: {len(publications_dict)}')

        pubs_graph = PublicationsGraph()
        for pub_id in publications_dict:
            pubs_graph.add_vertex(pub_id)

        self._dump_to_csv(publications_dict)
        self.__run_deduplication_script()

        path_to_deduplication_module = os.path.join(self._root_path, 'deduplication')
        possible_duplicates_path = os.path.join(path_to_deduplication_module, '_manual_dedup.csv')
        true_duplicates_path = os.path.join(path_to_deduplication_module, '_true_pairs.csv')

        false_positive = 0
        true_positive = 0
        false_negative = 0
        true_negative = 0

        with open(true_duplicates_path, 'r', encoding='utf-8') as true_pairs_csv:
            true_pairs_csv.readline()
            reader = csv.DictReader(true_pairs_csv,
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
                pubs_graph.add_edge(id_1, id_2)

                # testing logic
                if publications_dict[id_1].doi == publications_dict[id_2].doi:
                    true_positive += 1
                    continue

                filename = os.path.join(path_to_deduplication_module, 'cases', f'case-{n}.pdf')
                res_json = {}
                res_json['doc_1'] = publications_dict[id_1].to_dict()
                res_json['doc_2'] = publications_dict[id_2].to_dict()
                res_json['decision'] = 'DUPLICATES'
                res_json['state'] = 1
                config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
                pdfkit.from_string(json2html.convert(res_json), filename, configuration=config)
                # pprint(publications_dict[id_1].to_dict())
                # pprint(publications_dict[id_2].to_dict())
                # testing logic

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

        connected_components = pubs_graph.connected_components()

        unique_pubs_ids = set()
        for component in connected_components:
            base_pub = self._merge_publications(*[publications_dict[pub_id] for pub_id in component])
            component.discard(base_pub.id)

            publications_dict[base_pub.id] = deepcopy(base_pub)
            unique_pubs_ids.add(base_pub.id)

        # unique_cites_path = os.path.join(path_to_deduplication_module, '_unique_citations.csv')
        # os.remove(unique_cites_path)
        # os.remove(possible_duplicates_path)
        # os.remove(os.path.join(path_to_deduplication_module, '_dump_tmp.csv'))

        for pub_id in unique_pubs_ids:
            yield publications_dict[pub_id]

    def _merge_publications(self, *pubs) -> Document:
        if len(pubs) == 1:
            return pubs[0]

        base_pub = self._choose_best(*pubs)

        for p in pubs:
            if p.id != base_pub.id:
                base_pub.add_version(p)

        return base_pub

    @staticmethod
    def _choose_best(*pubs) -> Document:
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

        if float(row['author']) >= 0.5 and row['title'] == '1':
            return True
        if row['title'] == '1' and row['abstract'] == '1' and row['year'] == '1':
            return True
        if float(row['author']) >= 0.5 and row['title'] == '1' and row['abstract'] == '1':
            return True

        return False

    def _dump_to_csv(self, publications: Dict[int, Document]):
        # TODO: add env variable for path to deduplication raw dump

        path_to_dump = os.path.join(self._root_path, 'deduplication', '_dump_tmp.csv')

        with open(path_to_dump, 'w', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=Document.csv_keys())
            writer.writeheader()

            for pub_id in publications:
                writer.writerow(publications[pub_id].to_csv())

    def __run_deduplication_script(self):
        print('starting deduplication...')
        p = subprocess.run(['Rscript', self._path_to_deduplication_script], capture_output=True, text=True,
                           cwd=os.path.join(self._root_path, 'deduplication'))
        p.check_returncode()
