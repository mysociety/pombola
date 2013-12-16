#!/usr/bin/env python

import sys
import csv
import os
import re

os.environ['DJANGO_SETTINGS_MODULE'] = 'pombola.settings'

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../../../..'
    )
)

from mapit import models
from django.core.exceptions import ObjectDoesNotExist

class PollUnitImporter(object):

    cached_states = {}
    cached_lgas = {}
    cached_wards = {}

    cached_poll_unit_code_type = None
    cached_ward_type = None
    cached_nigeria = None
    cached_current_generation = None

    def process(self, filename):
        print "Looking at '{0}'".format(filename)

        for row in self.get_rows(filename):
            self.process_row(row)


    def get_rows(self, filename):
        fh = open(filename, 'r')
        rows = csv.DictReader(fh)
        return rows


    def process_row(self, row):

        # print row

        try:
            state = self.process_state_for_row(row)
            lga   = self.process_lga_for_row(row, state=state)
            ward  = self.process_ward_for_row(row, lga=lga)
        except ObjectDoesNotExist:
            sys.stderr.write(str(row) + "\n")


    def process_state_for_row(self, row):
        name = row['STATE NAME']
        code = self.tidy_up_code(row['STATE CODE'])

        if code in self.cached_states:
            return self.cached_states[code]

        print "Loading %s" % name

        # Should find all of these
        state = models.Area.objects.get(name__iexact=name, type__code='STA')

        # Check that the code has been added
        state.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        self.cached_states[code] = state
        return self.cached_states[code]


    def process_lga_for_row(self, row, state):
        name = row['LGA NAME']
        code = self.tidy_up_code(row['LGA CODE'], state)

        if code in self.cached_lgas:
            return self.cached_lgas[code]

        print "  Loading %s" % name

        # Should find all of these
        lga = models.Area.objects.get(name__iexact=name, type__code='LGA')

        # Check that the code has been added
        lga.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        self.cached_lgas[code] = lga
        return self.cached_lgas[code]


    def process_ward_for_row(self, row, lga):
        name = row['WARD NAME']
        code = self.tidy_up_code(row['WARD CODE'], lga)

        if code in self.cached_wards:
            return self.cached_wards[code]

        print "    Loading %s" % name

        # Create if needed, not expected to exist already
        ward, created = models.Area.objects.get_or_create(
            name=name,
            type=self.ward_type,
            parent_area=lga,
            country=self.nigeria,
            defaults={
                "generation_low": self.current_generation,
                "generation_high": self.current_generation,
            }
        )

        # Check that the code has been added
        ward.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        self.cached_wards[code] = ward
        return self.cached_wards[code]


    def tidy_up_code(self, code, parent=None):
        # strip leading zeros
        code = re.sub(r'^0+', '', code).upper()

        # Append to parent code
        if parent:
            parent_code = parent.codes.get(type=self.poll_unit_code_type).code
            code = parent_code + ':' + code

        return code


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


    @property
    def nigeria(self):
        if not self.cached_nigeria:
            self.cached_nigeria = models.Country.objects.get(
                name="Nigeria",
            )

        return self.cached_nigeria


    @property
    def ward_type(self):
        if not self.cached_ward_type:
            self.cached_ward_type, created = models.Type.objects.get_or_create(
                code="WRD",
                defaults={
                    "description": "Ward"
                }
            )

        return self.cached_ward_type



    @property
    def current_generation(self):
        if not self.cached_current_generation:
            self.cached_current_generation = models.Generation.objects.get(
                active=True
            )

        return self.cached_current_generation




for filename in sys.argv[1:]:
    importer = PollUnitImporter()
    importer.process(filename)

