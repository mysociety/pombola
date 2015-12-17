#!/usr/bin/env python

import json
import sys
import csv


csv_columns = (
    "slug",
    "original_line", 
    "type",
    "organisation", 
    "title", 
    "subtitle",
    "place",
    "start_date",
    "end_date", 
)

writer = csv.DictWriter( sys.stdout, csv_columns )
writer.writeheader()


def process(filename):
    data = json.loads( open(filename, 'r').read() )

    for pos in data.get('positions', []):
        out = pos.copy()
        out.update(slug=data['slug'])

        # because Python's CSV chockes otherwise :(
        utf8_out = {}
        for key in out.keys():
            utf8_out[key] = out[key].encode('utf-8')

        # print out
        writer.writerow(utf8_out)
        # break


for filename in sys.argv[1:]:
    # print filename
    process( filename )

