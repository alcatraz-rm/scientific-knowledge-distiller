# Search engine

This module contains search engine.

Search logic can be accessed through `Search` class, it can be found in [search.py](./search.py). For new search you have to create new `Search` instance.

Constructor of `Search`:
```python
def __init__(
        self,
        query: str,
        limit: int = 1000,
        remove_duplicates: bool = True,
        remove_without_title: bool = True,
        fill_abstracts: bool = True,
        sources: tuple = (
            SupportedSources.ARXIV,
            SupportedSources.CORE,
            SupportedSources.INTERNET_ARCHIVE,
            SupportedSources.SEMANTIC_SCHOLAR,
            SupportedSources.UNPAYWALL,
            SupportedSources.CROSSREF,
            SupportedSources.OPENALEX,
            SupportedSources.PAPERS_WITH_CODE,
        )
):
```

| option               | type                   | default value      | description                                                                              |
|----------------------|------------------------|--------------------|------------------------------------------------------------------------------------------|
| `query`                | `str`                    |                    | Search query                                                                             |
| `limit`                | `int`                    | `1000`               | Limit of documents to find (before deduplication)                                        |
| `remove_duplicates`    | `bool`                   | `True`               | If set to True, duplicates will be automatically removed                                 |
| `remove_without_title` | `bool`                   | `True`               | If set to True, papers without titles will be automatically removed                      |
| `fill_abstracts`       | `bool`                   | `True`               | If set to True, system will try to find abstracts for those articles where it is missing  |
| `sources`              | `Tuple[SupportedSource]` | can be found above | Tuple of sources to use, by default there are all of supported sources                                                                                         |

To perform search, you should call `perform` method. To get results, you should call results `method`.

Example of using `Search`:
```python
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from search_engine import Search
from search_engine.databases.database_client import SupportedSources
from utils.utils import find_root_directory

root_path = find_root_directory()
load_dotenv(dotenv_path=Path(os.path.join(root_path, '.env')))

query = 'bert for semantic textual similarity task'
limit = 5000

s = Search(
    query,
    limit=limit,
    remove_duplicates=True,
    remove_without_title=True,
    fill_abstracts=True,
    sources=(
        SupportedSources.ARXIV,
        SupportedSources.CORE,
        SupportedSources.CROSSREF,
        SupportedSources.INTERNET_ARCHIVE,
        SupportedSources.SEMANTIC_SCHOLAR,
        SupportedSources.UNPAYWALL,
        SupportedSources.OPENALEX,
        SupportedSources.PAPERS_WITH_CODE,
    )
)

start_time = time.time()
s.perform()
results = list(s.results())
end_time = time.time()
print(f'elapsed time: {end_time - start_time}')
print(f'total results after deduplication: {len(results)}')

for paper in results:
    print(paper.title)

```
