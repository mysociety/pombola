#!/usr/bin/env python

import csv
from optparse import make_option
from os.path import dirname, join
import re

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from mapit import models


class Command(BaseCommand):

    help = "Add polling unit codes from a CSV file to MapIt areas"

    option_list = BaseCommand.option_list + (
        make_option(
            '--ignore-wards',
            action='store_true',
            default=False,
            help="Don't process wards"
        ),
        make_option(
            '--delete-existing-pu-codes',
            action='store_true',
            default=False,
            help="Removing existing PU codes (not names) before importing",
        ),
        make_option(
            '--delete-existing-wards',
            action='store_true',
            default=False,
            help="Removing existing wards before importing",
        ),
    )

    def handle(self, *args, **options):
        atlas_filename = join(
            dirname(__file__), '..', '..', 'data',
            'Nigeria - Political Atlas for SYE.csv'
        )
        importer = PollUnitImporter(options)
        importer.process(atlas_filename)


class PollUnitImporter(object):

    cached_states = {}
    cached_lgas = {}
    cached_wards = {}

    cached_poll_unit_code_type = None
    cached_poll_name_code_type = None
    cached_ward_type = None
    cached_nigeria = None
    cached_current_generation = None

    def __init__(self, options):
        self.options = options

    def process(self, filename):
        print "Looking at '{0}'".format(filename)

        if self.options['delete_existing_pu_codes']:
            self.poll_unit_code_type.codes.all().delete()

        if self.options['delete_existing_wards']:
            self.ward_type.areas.all().delete()

        for row in self.get_rows(filename):
            self.process_row(row)

    def get_rows(self, filename):
        fh = open(filename, 'r')
        rows = csv.DictReader(fh)
        return rows


    def get_area(self, **kwargs):
        all = models.Area.objects.filter(**kwargs).distinct('id').order_by('id')
        if all.count() == 0:
            raise ObjectDoesNotExist()
        elif all.count() > 1:
            raise Exception("Multiple matches for %s" % str(kwargs))
        else:
            return all[0]

    def process_row(self, row):

        # print row

        state = self.process_state_for_row(row)
        if row['LGA NAME'].strip():
            lga = self.process_lga_for_row(row, state=state)
            if not self.options['ignore_wards']:
                self.process_ward_for_row(row, lga=lga)

    def process_state_for_row(self, row):
        name = row['STATE NAME'].strip()
        code = self.tidy_up_code(row['STATE CODE'])

        if code in self.cached_states:
            return self.cached_states[code]

        print "Loading %s" % name

        # Should find all of these
        state = self.get_area(names__name__iexact=name, type__code='STA')

        # Check that the code has been added
        state.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        self.cached_states[code] = state
        return self.cached_states[code]

    def process_lga_for_row(self, row, state):
        name = row['LGA NAME'].strip()
        code = self.tidy_up_code(row['LGA CODE'], state)

        if code in self.cached_lgas:
            return self.cached_lgas[code]

        print "  Loading %s" % name

        # Should find all of these
        lga = self.get_area(names__name__iexact=name, type__code='LGA', parent_area=state)

        # Check that the code has been added
        lga.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        self.cached_lgas[code] = lga
        return self.cached_lgas[code]

    def process_ward_for_row(self, row, lga):
        name = row['WARD NAME'].strip()
        code = self.tidy_up_code(row['WARD CODE'], lga)

        if code in self.cached_wards:
            return self.cached_wards[code]

        print "    Loading %s" % name

        # Create if needed, not expected to exist already
        ward, created = models.Area.objects.get_or_create(
            names__name=name,
            type=self.ward_type,
            parent_area=lga,
            country=self.nigeria,
            defaults={
                "name": name,
                "generation_low": self.current_generation,
                "generation_high": self.current_generation,
            }
        )

        # Check that the code has been added
        ward.codes.get_or_create(
            type=self.poll_unit_code_type,
            code=code,
        )

        ward.names.get_or_create(
            type=self.poll_unit_name_type,
            name=name,
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
    def poll_unit_name_type(self):
        if not self.cached_poll_name_code_type:
            self.cached_poll_name_code_type, created = models.NameType.objects.get_or_create(
                code = 'poll_unit',
                defaults = {
                    'description': "The name given in the data set of Polling Unit Numbers"
                }
            )

        return self.cached_poll_name_code_type

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
