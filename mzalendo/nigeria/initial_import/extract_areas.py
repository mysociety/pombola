#!/usr/bin/env python

import json
import sys
import re


areas_found = set()

def process(filename):
    data = json.loads( open(filename, 'r').read() )
    # print data

    for pos in data['positions']:        
        place = pos.get('place')
        if place:
            place = re.sub( '[,&]', '/', place)
            place = re.sub( ' - ', '/', place)
            place = re.sub( '\s*/\s*', ' / ', place)
            # entry = pos['title'] + ': ' + place
            entry = place
            areas_found.add(entry)


for filename in sys.argv[1:]:
    # print filename
    process( filename )
    # break


for p in sorted(areas_found):
    print p

