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

    all_lgas = set()
    duplicates = ()

    def process(self, filename):
        print "Looking at '{0}'".format(filename)
        self.load_lgas(filename)
        self.find_duplicates_in_csv()


    def load_lgas(self, filename):
        for row in self.get_rows(filename):
            self.all_lgas.add(
                (row['LGA NAME'], row['STATE NAME'])
            )


    def find_duplicates_in_csv(self):
        # lga_name => state
        seen = {}

        for lga_name, state_name in self.all_lgas:
            if lga_name in seen and seen[lga_name] != state_name:
                print "Duplicate: LGA {0} is also in states {1} and {2}".format(lga_name, seen[lga_name], state_name)
            seen[lga_name] = state_name


    def get_rows(self, filename):
        fh = open(filename, 'r')
        rows = csv.DictReader(fh)
        return rows



for filename in sys.argv[1:]:
    checker = LgaNameChecker()
    checker.process(filename)

