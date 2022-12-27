import csv
import os.path
import subprocess
from typing import Iterable

from search_engine.databases.database import SearchResult


class Deduplicator:
    def __init__(self):
        self._path_to_deduplication_script = os.path.join(os.getcwd(), 'deduplication', 'deduplicate.r')

    def deduplicate(self, *iterables):
        Deduplicator._dump_to_csv(*iterables)

        p = subprocess.run(['Rscript', self._path_to_deduplication_script], capture_output=True, text=True,
                           cwd=os.path.join(os.getcwd(), 'deduplication'))

        print("stdout:", p.stdout)
        print("stderr:", p.stderr)

    @staticmethod
    def _dump_to_csv(*iterables):
        # TODO: add env variable for path to deduplication raw dump
        path_to_dump = os.path.join(os.getcwd(), 'deduplication', '_dump_tmp.csv')

        with open(path_to_dump, 'w', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=SearchResult.csv_keys())
            writer.writeheader()

            for publication_set in iterables:
                for publication in publication_set:
                    writer.writerow(publication.to_csv())
