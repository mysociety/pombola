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

    def process(self, filename):
        print "Looking at '{0}'".format(filename)




for filename in sys.argv[1:]:
    importer = PollUnitImporter()
    importer.process(filename)

