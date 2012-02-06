#!/usr/bin/env python

import sys
import csv
import os
import decimal

os.environ['DJANGO_SETTINGS_MODULE'] = 'mzalendo.settings'
sys.path.append('../../../')
sys.path.append('../../')

from mzalendo.core.models import Place
from mzalendo.place_data.models import Entry

filename = sys.argv[1]
csv_file = open(filename, 'rU')

csv_reader = csv.DictReader(csv_file, dialect='excel')

for row in csv_reader:
    data_row = Entry()

    place_slug = row['slug'].strip()
    data_row.place = Place.objects.get(slug=place_slug)

    data_row.population_male = int(row['Male'])
    data_row.population_female = int(row['Female'])
    data_row.population_total = int(row['Total'])
    data_row.households_total = int(row['Households'])
    data_row.area = decimal.Decimal(row['Area in Sq. Km.'])

    data_row.save()
