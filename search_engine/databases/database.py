import random
import string
from copy import deepcopy
from datetime import datetime
from pprint import pprint
from typing import Iterator, Union
from enum import StrEnum

import arxiv


class SupportedSources(StrEnum):
    SEMANTIC_SCHOLAR = 'semantic_scholar'
    CORE = 'core'
    ARXIV = 'arxiv'
    UNPAYWALL = 'unpaywall'
    GOOGLE_SCHOLAR = 'google_scholar'
    INTERNET_ARCHIVE = 'internet_archive'


class Author:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name


class SearchResult:
    def __init__(self, raw_data: Union[dict, arxiv.Result], source: SupportedSources):
        assert raw_data is not None, 'Incorrect input data'

        self._title = ''
        self._abstract = ''
        self._publication_date = None
        self._authors = []
        self._source = ''
        self._raw_data = {}
        self._journal = ''
        self._volume = ''
        self._doi = ''
        self._urls = []

        self._raw_data = deepcopy(raw_data)
        self._load_from(raw_data, source)

        self.__salt = ''.join(random.choices(string.ascii_uppercase + string.digits, k=64))
        self._id = f'id{hash((self.__salt, self._title, self._doi, self._abstract, self._source))}'

    @property
    def empty_fields(self) -> int:
        counter = 0
        fields = (
            self._title,
            self._abstract,
            self._publication_date,
            self._authors,
            self._journal,
            self._volume,
            self._doi,
            self._urls
        )

        for field in fields:
            if not field:
                counter += 1

        return counter

    @property
    def title(self) -> str:
        return self._title

    @property
    def abstract(self) -> str:
        return self._abstract

    @property
    def year(self) -> int:
        if self._publication_date:
            return self._publication_date.year
        return 0

    @property
    def id(self) -> str:
        return self._id

    @property
    def publication_date(self) -> datetime:
        return self._publication_date

    # returns a dict to dump to csv for deduplication
    def to_csv(self) -> dict:
        return dict(
            author=','.join([author.name for author in self._authors]) if self._authors else '',
            year=self.year,
            journal=self._journal if self._journal else '',
            doi=self._doi if self._doi else '',
            title=self._title.replace('\n', ' ') if self._title else '',
            pages=self._volume if self._volume else '',  # TODO
            volume=self._volume if self._volume else '',
            number=0,  # TODO
            abstract=self._abstract.replace('\n', ' ') if self._abstract else '',
            record_id=self._id,
            isbn='',
            label='',
            source=self._source
        )

    @staticmethod
    def csv_keys() -> tuple:
        return (
            'author',
            'year',
            'journal',
            'doi',
            'title',
            'pages',
            'volume',
            'number',
            'abstract',
            'record_id',
            'isbn',
            'label',
            'source',
        )

    def _load_from(self, raw_data: Union[dict, arxiv.Result], source: SupportedSources):
        match source:
            case SupportedSources.SEMANTIC_SCHOLAR:
                self._load_from_semantic_scholar(raw_data)
            case SupportedSources.CORE:
                self._load_from_core(raw_data)
            case SupportedSources.ARXIV:
                self._load_from_arxiv(raw_data)
            case SupportedSources.UNPAYWALL:
                self._load_from_unpaywall(raw_data)
            case SupportedSources.GOOGLE_SCHOLAR:
                self._load_from_google_scholar(raw_data)
            case SupportedSources.INTERNET_ARCHIVE:
                self._load_from_internet_archive(raw_data)
            case _:
                raise Exception(f'Unsupported source: {source}')

    def _load_from_semantic_scholar(self, raw_data: dict):
        self._source = SupportedSources.SEMANTIC_SCHOLAR
        self._title = raw_data.get('title', '')
        self._abstract = raw_data.get('abstract', '')
        self._urls.append(raw_data.get('url'))

        raw_journal = raw_data.get('journal')

        if raw_journal and 'name' in raw_journal and 'volume' in raw_journal:
            self._journal = raw_journal.get('name')
            self._volume = raw_journal.get('volume')

        raw_ids = raw_data.get('externalIds')
        if raw_ids:
            self._doi = raw_ids.get('DOI', '')

        raw_pub_date = raw_data.get('publicationDate', '')
        if raw_pub_date:
            self._publication_date = datetime.strptime(raw_pub_date, "%Y-%m-%d")

        for raw_author in raw_data['authors']:
            self._authors.append(Author(raw_author['name']))

    def _load_from_core(self, raw_data: dict):
        self._source = SupportedSources.CORE
        self._title = raw_data.get('title', '')
        self._abstract = raw_data.get('abstract', '')
        self._doi = raw_data.get('doi', '')
        self._urls = [raw_data.get('downloadUrl')]

        raw_pub_date = raw_data.get('publishedDate', '')
        if raw_pub_date:
            raw_pub_date = raw_pub_date.split('T')[0]
            self._publication_date = datetime.strptime(raw_pub_date, "%Y-%m-%d")

        for raw_author in raw_data['authors']:
            self._authors.append(Author(raw_author['name']))

        raw_journal = raw_data.get('journals')

        if raw_journal and 'title' in raw_journal[0]:
            self._journal = raw_journal[0].get('title')

    def _load_from_arxiv(self, raw_data: arxiv.Result):
        self._source = SupportedSources.ARXIV
        self._title = raw_data.title
        self._abstract = raw_data.summary
        self._doi = raw_data.doi if raw_data.doi else ''
        self._urls = [raw_data.pdf_url] + [link.href for link in raw_data.links]
        self._publication_date = raw_data.published
        self._journal = raw_data.journal_ref

        for raw_author in raw_data.authors:
            self._authors.append(Author(raw_author.name))

    def _load_from_unpaywall(self, raw_data: dict):
        self._source = SupportedSources.UNPAYWALL
        self._title = raw_data.get('title', '')
        self._doi = raw_data.get('doi', '')
        self._urls = [raw_data.get('doi_url')]

        raw_pub_date = raw_data.get('publication_date', '')
        if raw_pub_date:
            self._publication_date = datetime.strptime(raw_pub_date, "%Y-%m-%d")
        self._journal = raw_data.get('journal_name', '')

        raw_authors = raw_data.get('z_authors', [])
        if not raw_authors:
            return

        for raw_author in raw_authors:
            if 'family' in raw_author and 'given' in raw_author:
                self._authors.append(Author(f'{raw_author["family"]}, {raw_author["given"][0]}.'))
            elif 'given' in raw_author and 'family' not in raw_author:
                self._authors.append(Author(raw_author['given']))
            elif 'family' in raw_author and 'given' not in raw_author:
                self._authors.append(Author(raw_author['family']))
            elif 'name' in raw_author:
                self._authors.append(Author(raw_author['name']))
            else:
                print(raw_author)

    def _load_from_google_scholar(self, raw_data: dict):
        self._source = SupportedSources.GOOGLE_SCHOLAR

        bib_info = raw_data.get('bib')

        if bib_info:
            self._title = bib_info.get('title', '')
            self._abstract = bib_info.get('abstract', '')
            self._authors = [Author(author) for author in bib_info.get('author')]
            self._publication_date = datetime.strptime(bib_info.get('pub_year'), '%Y')
        self._urls = [raw_data.get('pub_url')]

    def _load_from_internet_archive(self, raw_data: dict):
        self._source = SupportedSources.INTERNET_ARCHIVE
        biblio_data = raw_data.get('biblio')
        self._title = biblio_data.get('title', '')
        abstracts = raw_data.get('abstracts', [])
        self._abstract = abstracts[0]['body'] if abstracts else ''
        self._doi = biblio_data.get('doi', '')
        self._urls = [link['access_url'] for link in raw_data.get('access', [])]

        if 'release_date' in biblio_data:
            self._publication_date = datetime.strptime(biblio_data.get('release_date'), "%Y-%m-%d")
        elif 'release_year' in biblio_data:
            self._publication_date = datetime.strptime(str(biblio_data.get('release_year')), '%Y')

        self._journal = biblio_data.get('publisher', '')

        for raw_author in biblio_data.get('contrib_names', []):
            self._authors.append(Author(raw_author))

    def __str__(self) -> str:
        return self._title


class DatabaseClient:
    def __init__(self):
        pass

    def search_publications(self, query: str, limit: int = 100) -> Iterator[SearchResult]:
        pass
