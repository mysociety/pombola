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

class LgaNameChecker(object):

    # tuples like (lga_name, state_name)
    all_lgas = set()
    duplicates = set()
    matched = set()
    unmatched = set()

    duplicate_lga_names = set() # just lga_name
    matched_area_ids = set() # just mapit area ids

    def process(self, filename):
        print "Looking at '{0}'".format(filename)
        self.load_lgas(filename)
        self.find_duplicates_in_csv()
        self.set_name_for_unmatched()
        self.list_unmatched()


    def load_lgas(self, filename):
        with open(filename, 'r') as fh:
            rows = csv.DictReader(fh)
            for row in rows:
                self.all_lgas.add(
                    (row['LGA NAME'], row['STATE NAME'])
                )


    def find_duplicates_in_csv(self):
        # lga_name => state
        seen = {}

        for lga_name, state_name in self.all_lgas:
            if lga_name in seen and seen[lga_name] != state_name:
                print "Duplicate: LGA {0} is also in states {1} and {2}".format(lga_name, seen[lga_name], state_name)
                self.duplicate_lga_names.add(lga_name)
            seen[lga_name] = state_name


    def partition_lgas(self):
        self.matched.clear()
        self.unmatched.clear()
        self.matched_area_ids.clear()

        for lga_name, state_name in self.all_lgas:

            entry = (lga_name, state_name)

            # Handle duplicates later
            if lga_name in self.duplicate_lga_names:
                self.duplicates.add(entry)
                continue

            try:
                lga_area = models.Area.objects.get(names__name__iexact=lga_name, type__code='LGA')
            except ObjectDoesNotExist:
                lga_area = None

            if lga_area and lga_area.id in self.matched_area_ids:
                print "WARNING: {0} already matched".format(lga_area)
                lga_area = None

            if lga_area:
                # print "Hit  %s" % str(entry)
                self.matched.add(entry)
                self.matched_area_ids.add(lga_area.id)
            else:
                # print "Miss %s" % str(entry)
                self.unmatched.add(entry)


    def set_name_for_unmatched(self):
        for match_length in [4,3,2]:

            self.partition_lgas()

            done_count = 0
            total_count = len(self.unmatched)

            for lga_name, state_name in self.unmatched:
                done_count += 1
                print "--- {0} in {1} ({2} of {3})---".format(lga_name, state_name, done_count, total_count)


                # get the first bit of the word and match on that, should narrow field enough for a replacement to be created.
                match_text = lga_name.split(' ')[0][:match_length]

                self.match_lga_to_area(lga_name=lga_name, match_text=match_text)



    def match_lga_to_area(self, match_text, lga_name):

        name_type, created = models.NameType.objects.get_or_create(
            code = 'poll_unit',
            defaults = {
                'description': "The name given in the data set of Polling Unit Numbers"
            }
        )

        all_possibles = list(models.Area.objects.filter(names__name__icontains=match_text, type__code='LGA').order_by('name'))
        possibles = [x for x in all_possibles if x.id not in self.matched_area_ids]

        if not len(possibles): return

        counter = 1

        for possible in possibles:
            print counter, possible.name
            counter += 1

        print "Choose one of above (or blank to skip):",
        counter_chosen = raw_input()

        if counter_chosen:
            choice = possibles[int(counter_chosen) - 1]
            choice.names.create(type=name_type, name=lga_name)
            self.matched_area_ids.add(choice.id)

    def list_unmatched(self):
        self.partition_lgas()

        for lga_name, state_name in self.unmatched:
            print lga_name

        for area in models.Area.objects.filter(type__code='LGA').order_by('name'):
            if area.id in self.matched_area_ids: continue
            print area.name




for filename in sys.argv[1:]:
    checker = LgaNameChecker()
    checker.process(filename)

