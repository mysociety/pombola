#!/usr/bin/env python

import sys
import csv
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pombola.settings'

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../../../..'
    )
)

from mapit import models

class PollUnitImporter(object):

    cached_states = {}
    cached_poll_unit_code_type = None

    def process(self, filename):
        print "Looking at '{0}'".format(filename)

        count = 0
        for row in self.get_rows(filename):
            self.process_row(row)
            count += 1
            if count > 10: break



    def get_rows(self, filename):
        fh = open(filename, 'r')
        rows = csv.DictReader(fh)
        return rows

    def process_row(self, row):
        print row
        state = self.process_state_for_row(row)

    def process_state_for_row(self, row):
        name = row['STATE NAME']
        code = row['STATE CODE']

        if code in self.cached_states:
            return self.cached_states[code]

        # Should find all of these
        state = models.Area.objects.get(name__iexact=name)

        # Check that the code has been added
        state.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        self.cached_states[code] = state
        return self.cached_states[code]

    @property
    def poll_unit_code_type(self):
        if not self.cached_poll_unit_code_type:
            self.cached_poll_unit_code_type, created = models.CodeType.objects.get_or_create(
                code="poll_unit",
                defaults={
                    "description": "Polling Unit Number"
                }
            )

        return self.cached_poll_unit_code_type




for filename in sys.argv[1:]:
    importer = PollUnitImporter()
    importer.process(filename)

