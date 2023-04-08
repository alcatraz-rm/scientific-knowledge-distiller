import logging
import random
import string
import threading
from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import Iterator, Union
# from googletrans import Translator
from uuid import UUID

import arxiv


class SupportedSources(Enum):
    SEMANTIC_SCHOLAR = 'semantic_scholar'
    CORE = 'core'
    ARXIV = 'arxiv'
    UNPAYWALL = 'unpaywall'
    GOOGLE_SCHOLAR = 'google_scholar'
    INTERNET_ARCHIVE = 'internet_archive'
    CROSSREF = 'crossref'
    # DBLP = 'dblp'
    OPENALEX = 'openalex'
    PAPERS_WITH_CODE = 'papers_with_code'


class SearchStatus(Enum):
    DEFAULT = 0
    WORKING = 1
    FINISHED = 2
    WAITING = 3


class Author:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name


class Document:
    def __init__(self, raw_data: Union[dict, arxiv.Result], source: SupportedSources):
        assert raw_data is not None, 'Incorrect input data'

        self._title = ''
        self._abstract = ''
        self._publication_date = None
        self._authors = []
        self._source = source
        self._raw_data = {}
        self._journal = ''
        self._volume = ''
        self._doi = ''
        self._lang = ''
        self._urls = []

        self._versions = []

        self._raw_data = deepcopy(raw_data)
        self._load_from(raw_data, source)

        self.__salt = ''.join(random.choices(string.ascii_uppercase + string.digits, k=64))
        self._id = f'id{hash((self.__salt, self._title, self._doi, self._abstract, self._source))}'

        if self._title is None:
            self._title = ''
        self._title.strip()
        self._title = self._title.replace('\n', ' ')

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
        return self._title if self._title else ''

    @property
    def source(self) -> SupportedSources:
        return self._source

    @property
    def journal(self) -> str:
        return self._journal

    @property
    def urls(self) -> list:
        return self._urls

    @property
    def doi(self) -> str:
        return self._doi

    @property
    def abstract(self) -> str:
        return self._abstract if self._abstract else ''

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

    # @property
    # def lang(self) -> str:
    #     return self._lang

    @property
    def versions(self) -> list:
        return self._versions

    # returns a dict to dump to csv for deduplication
    def to_csv(self) -> dict:
        return dict(
            author=','.join([author.name for author in self._authors if author.name]) if self._authors else '',
            year=self.year,
            journal=self._journal if self._journal else '',
            doi=self._doi if self._doi else '',
            title=self._title.replace('\n', ' ') if self._title else '',
            pages='',
            volume='',
            number=0,  # TODO
            abstract=self._abstract.replace('\n', ' ') if self._abstract else '',
            record_id=self._id,
            isbn='',
            label='',
            source=self._source
        )

    def to_dict(self) -> dict:
        versions = deepcopy(self._versions)
        for n in range(len(versions)):
            versions[n]['source'] = str(versions[n]['source'])
            versions[n]['publication_date'] = str(versions[n]['publication_date'])

        return dict(
            authors=[str(author) for author in self._authors],
            title=self._title,
            publication_date=str(self._publication_date),
            source=str(self._source),
            journal=self._journal,
            volume=self._volume,
            doi=self._doi,
            urls=self._urls,
            id=self._id,
            abstract=self._abstract,
            versions=versions
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

    def add_version(self, other):
        self._versions.append(
            {
                'year': other.year,
                'source': other.source,
                'title': other.title,
                'journal': other.journal,
                'urls': other.urls,
                'doi': other.doi,
                'publication_date': other.publication_date
            }
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
            case SupportedSources.CROSSREF:
                self._load_from_crossref(raw_data)
            # case SupportedSources.DBLP:
            #     self._load_from_dblp(raw_data)
            case SupportedSources.OPENALEX:
                self._load_from_openalex(raw_data)
            case SupportedSources.PAPERS_WITH_CODE:
                self._load_from_papers_with_code(raw_data)
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

        is_oa = raw_data.get('isOpenAccess')
        if is_oa:
            oa_pdf_url = raw_data.get('openAccessPdf', {})
            if oa_pdf_url:
                oa_pdf_url = oa_pdf_url.get('url', '')
                if oa_pdf_url:
                    self._urls.append(oa_pdf_url)


    def _load_from_core(self, raw_data: dict):
        self._source = SupportedSources.CORE
        self._title = raw_data.get('title', '')

        if self._title:
            self._title = self._title.replace('\n', '')

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
            raw_authors = []

        for raw_author in raw_authors:
            if 'family' in raw_author and 'given' in raw_author:
                self._authors.append(Author(f'{raw_author["family"]}, {raw_author["given"][0]}.'))
            elif 'given' in raw_author and 'family' not in raw_author:
                self._authors.append(Author(raw_author['given']))
            elif 'family' in raw_author and 'given' not in raw_author:
                self._authors.append(Author(raw_author['family']))
            elif 'name' in raw_author:
                self._authors.append(Author(raw_author['name']))
            # else:
            #     print(raw_author)

    def _load_from_google_scholar(self, raw_data: dict):
        self._source = SupportedSources.GOOGLE_SCHOLAR

        bib_info = raw_data.get('bib')

        if bib_info:
            self._title = bib_info.get('title', '')
            self._abstract = bib_info.get('abstract', '')
            self._authors = [Author(author) for author in bib_info.get('author')]
            pub_year = bib_info.get('pub_year')
            if pub_year and pub_year != 'NA':
                self._publication_date = datetime.strptime(pub_year, '%Y')
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

    def _load_from_crossref(self, raw_data: dict):
        self._source = SupportedSources.CROSSREF
        self._title = raw_data.get('title', [''])[0]
        self._doi = raw_data.get('DOI', '')
        self._urls = [link['URL'] for link in raw_data.get('link', [])] + [raw_data.get('URL', '')]

        if 'published' in raw_data:
            raw_date = raw_data.get('published').get('date-parts')[0]
            if len(raw_date) == 3:
                self._publication_date = datetime(year=raw_date[0], month=raw_date[1], day=raw_date[2])
            else:
                self._publication_date = datetime(year=raw_date[0], month=1, day=1)

        raw_authors = raw_data.get('author', [])

        for raw_author in raw_authors:
            if 'family' in raw_author and 'given' in raw_author:
                self._authors.append(Author(f'{raw_author["family"]}, {raw_author["given"][0]}.'))
            elif 'given' in raw_author and 'family' not in raw_author:
                self._authors.append(Author(raw_author['given']))
            elif 'family' in raw_author and 'given' not in raw_author:
                self._authors.append(Author(raw_author['family']))
            elif 'name' in raw_author:
                self._authors.append(Author(raw_author['name']))

    # def _load_from_dblp(self, raw_data: dict):
    #     pass

    def _load_from_openalex(self, raw_data: dict):
        self._source = SupportedSources.OPENALEX
        self._title = raw_data.get('title')

        self._doi = raw_data.get('doi', '')
        if self._doi and 'https://doi.org/' in self._doi:
            self._doi = self._doi.replace('https://doi.org/', '')

        self._publication_date = datetime.strptime(raw_data.get('publication_date'), "%Y-%m-%d")
        ids = raw_data.get('ids')
        if ids:
            if 'openalex' in ids:
                self._urls.append(ids['openalex'])
            if 'doi' in ids:
                self._urls.append(ids['doi'])
        else:
            self._urls = [raw_data.get('id')]

        open_access = raw_data.get('open_access')
        if open_access['is_oa']:
            self._urls.append(open_access['oa_url'])

        for author in raw_data.get('authorships'):
            self._authors.append(Author(author['author']['display_name']))

        biblio = raw_data.get('biblio')
        if biblio and biblio.get('volume'):
            self._volume = biblio.get('volume')

        host_venue = raw_data.get('host_venue')
        if host_venue and host_venue.get('display_name'):
            self._journal = host_venue.get('display_name')

    def _load_from_papers_with_code(self, raw_data: dict):
        self._source = SupportedSources.PAPERS_WITH_CODE
        paper_info = raw_data.get('paper')
        self._title = paper_info.get('title')
        self._abstract = paper_info.get('abstract')

        self._urls.append(paper_info.get('url_pdf'))
        repository_info = raw_data.get('repository')
        if repository_info:
            self._urls.append(repository_info.get('url'))

        if paper_info['conference_url_pdf']:
            self._urls.append(paper_info['conference_url_pdf'])

        published = paper_info.get('published')
        if published:
            self._publication_date = datetime.strptime(published, "%Y-%m-%d")
        for author in paper_info.get('authors', []):
            self._authors.append(Author(author))

    def __str__(self) -> str:
        return self._title

    def __repr__(self) -> str:
        return self.title


class DatabaseClient:
    def __init__(self, source_name: SupportedSources):
        self._searches = {}
        self._name = source_name

    @property
    def name(self) -> SupportedSources:
        return self._name

    def _create_search(self, search_id: UUID, limit: int):
        with threading.Lock():
            self._searches[search_id] = {
                'status': SearchStatus.WORKING,
                'documents_to_pull': limit,
                'documents_pulled': 0,
                'kill_signal_occurred': False
            }

    def _change_status(self, status: SearchStatus, search_id: UUID):
        with threading.Lock():
            self._searches[search_id]['status'] = status
        logging.info(f'Status for {self.name} changed to {status}.')

    def _terminate(self, search_id: UUID):
        with threading.Lock():
            self._searches[search_id]['kill_signal_occurred'] = True
            self._searches[search_id]['status'] = SearchStatus.FINISHED

    def _documents_pulled(self, search_id: UUID) -> int:
        with threading.Lock():
            return self._searches[search_id]['documents_pulled']

    def _kill_signal_occurred(self, search_id: UUID):
        with threading.Lock():
            return self._searches[search_id]['kill_signal_occurred']

    # note: don't call this manually
    def send_kill_signal(self, search_id: UUID):
        with threading.Lock():
            self._searches[search_id]['kill_signal_occurred'] = True

    def documents_to_pull(self, search_id: UUID) -> int:
        with threading.Lock():
            return self._searches[search_id]['documents_to_pull']

    def change_limit(self, search_id: UUID, delta: int):
        with threading.Lock():
            self._searches[search_id]['documents_to_pull'] = max(
                0,
                self._searches[search_id]['documents_to_pull'] + delta
            )

            if delta < 0:
                self._searches[search_id]['documents_pulled'] -= delta

        if delta > 0:
            logging.info(f'Limit for {self.name} increased for {delta} documents.')

    def search_status(self, search_id: UUID) -> Union[SearchStatus, None]:
        with threading.Lock():
            search_info = self._searches.get(search_id)
            if not search_info:
                return
            return search_info['status']

    def search_publications(self, query: str, search_id: UUID, imit: int = 100) -> Iterator[Document]:
        pass
