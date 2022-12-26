from datetime import datetime
from typing import Iterator


class Author:
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name


class SearchResult:
    supported_sources = (
        'semantic_scholar',
        'core',
    )

    def __init__(self, raw_data=None, source: str = ''):
        if raw_data is None:
            raw_data = {}
        assert (isinstance(raw_data, dict) and len(raw_data) != 0 and source in SearchResult.supported_sources) or (
                    isinstance(raw_data, dict) and len(raw_data) == 0 and len(source) == 0), 'Incorrect input data'

        self._title = ''
        self._abstract = ''
        self._publication_date = None
        self._authors = []
        self._source = ''
        self._raw_data = {}

        if len(source) != 0:
            self._raw_data = raw_data
            self._load_from(raw_data, source)

    def title(self) -> str:
        return self._title

    def abstract(self) -> str:
        return self._abstract

    def publication_date(self) -> datetime:
        return self._publication_date

    def _load_from(self, raw_data: dict, source: str):
        if source == 'semantic_scholar':
            self._load_from_semantic_scholar(raw_data)
        elif source == 'core':
            self._load_from_core(raw_data)

    def _load_from_semantic_scholar(self, raw_data: dict):
        self._source = 'semantic_scholar'
        self._title = raw_data.get('title')
        self._abstract = raw_data.get('abstract')

        raw_pub_date = raw_data.get('publicationDate')
        if raw_pub_date:
            self._publication_date = datetime.strptime(raw_pub_date, "%Y-%m-%d")

        for raw_author in raw_data['authors']:
            self._authors.append(Author(raw_author['name']))

    def _load_from_core(self, raw_data: dict):
        self._source = 'core'
        self._title = raw_data.get('title')

        raw_pub_date = raw_data.get('publishedDate')
        if raw_pub_date:
            raw_pub_date = raw_pub_date.split('T')[0]
            self._publication_date = datetime.strptime(raw_pub_date, "%Y-%m-%d")

        for raw_author in raw_data['authors']:
            self._authors.append(Author(raw_author['name']))

    def __str__(self):
        return self._title


class DatabaseClient:
    def __init__(self):
        pass

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        pass
