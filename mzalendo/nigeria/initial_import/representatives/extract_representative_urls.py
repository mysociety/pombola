#!/usr/bin/env python

from bs4 import BeautifulSoup
from urlparse import urljoin
import sys

soup = BeautifulSoup( sys.stdin.read() )
# print soup.prettify()

# where the original html came from, use to resolve relative urls
base_url = 'http://www.nassnig.org/nass2/Princ_officers_all.php?title_sur=Hon.'

for link in soup.find_all('a'):
    if link.get_text().strip() != 'View My Constituency Page':
        continue
    print urljoin( base_url, link['href'] )

