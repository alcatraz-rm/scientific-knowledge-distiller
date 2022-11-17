from pprint import pprint
from scholarly import scholarly

# pprint(scholarly.search_keywords('blockchain'))
for citation in scholarly.search_pubs('blockchain'):
    print(citation['bib']['title'])
    input(':')
