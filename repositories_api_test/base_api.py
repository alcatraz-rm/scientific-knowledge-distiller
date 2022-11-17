from pprint import pprint

import requests

url = 'https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi'

response = requests.get(url, params={'func': 'PerformSearch', 'query': 'blockchain'}).text
pprint(response)
