#!/usr/bin/env python

# Take the json in the file given as first argument and convert it to the JSON
# format needed for import. Should do all cleanup of data and removal of
# unneeded entries too.

import sys
import json
import re
import urllib

from django.template.defaultfilters import slugify

class Converter(object):

    groupings = []

    def __init__(self, filename):
        self.filename = filename

    def convert(self):
        data = self.extract_data_from_json()

        self.extract_source(data)
        self.extract_entries(data)

        return self.produce_json()

    def extract_source(self, data):
        source_url = data['source']
        year = data['year']

        source_filename = re.sub(r'.*/(.*?)\.pdf', r'\1', source_url)
        source_name = urllib.unquote(source_filename).strip()

        self.source = {
            "name": source_name,
            "date": year + "-01-01",
        }

    def extract_entries(self, data):
        for register_entry in data['register']:
            for raw_category_name, entries in register_entry.items():
                # we only care about entries that are arrays
                if type(entries) != list or len(entries) == 0:
                    continue

                grouping = {
                    "source": self.source,
                    "entries": entries,
                }

                # Break up the name into sort_order and proper name
                sort_order, category_name = raw_category_name.strip().split('. ')
                grouping['category'] = {
                    "sort_order": sort_order,
                    "name": category_name,
                }

                # Work out who the person is
                grouping['person'] = {
                    "slug": self.mp_to_person_slug(register_entry['mp'])
                }

                self.groupings.append(grouping)

            break # just for during dev

    def mp_to_person_slug(self, mp):
        return slugify(mp)

    def produce_json(self):
        data = self.groupings
        out = json.dumps(data, indent=4, sort_keys=True)
        return re.sub(r' *$', '', out, flags=re.M)

    def extract_data_from_json(self):
        with open(self.filename) as fh:
            return json.load(fh)


if __name__ == "__main__":
    converter = Converter(sys.argv[1])
    output = converter.convert()
    print output