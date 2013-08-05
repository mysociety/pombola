#!/usr/bin/env python

import sys
import csv
import os
import decimal

os.environ['DJANGO_SETTINGS_MODULE'] = 'pombola.settings'
sys.path.append('../../../')
sys.path.append('../../')

from django.template.defaultfilters import slugify

from pombola.core.models import Place
from pombola.place_data.models import Entry

place_kind_slug = sys.argv[1]
filename = sys.argv[2]
csv_file = open(filename, 'rU')

csv_reader = csv.DictReader(csv_file, dialect='excel')

# Get rid of the padding around the fieldnames
csv_reader.fieldnames = [x.strip() for x in csv_reader.fieldnames]

for row in csv_reader:
    try:
        place_slug = row['slug'].strip()
    except KeyError:
        # If there's no slug column, try slugifying the name column
        # This will currently only happen on the Counties - the constituency
        # spreadsheet has slugs.
        # If we needed this to work for constituencies, we'd have to not add
        # -constituency on the end as they don't have that.
        place_slug = slugify(row['name'].strip()) + '-' + place_kind_slug
    
    # Check place with this slug exists and is of the right kind.
    try:
        place = Place.objects.get(slug=place_slug, kind__slug=place_kind_slug)
    except Place.DoesNotExist:
        print "Cannot find %s with slug %s, continuing with next place." % (place_kind_slug, place_slug)
        continue

    try:
        data_row = Entry.objects.get(place=place)
    except Entry.DoesNotExist:
        data_row = Entry()
        data_row.place = place

    data_row.population_male = int(row['Male Population'])
    data_row.population_female = int(row['Female Population'])
    data_row.population_total = int(row['Total Population'])
    data_row.population_rank = int(row['Population Rank 1=Highest'])
    data_row.gender_index = decimal.Decimal(row['Gender Ration Women:Men'])
    data_row.gender_index_rank = int(row['Women to Men Ratio Rank 1=Highest'])
    data_row.households_total = int(row['Number of Households'])
    data_row.average_household_size = decimal.Decimal(row['Average Houshold Size'])
    data_row.household_size_rank = int(row['Household Size Rank 1=Highest'])
    data_row.area = decimal.Decimal(row['Area in Sq. Km.'])
    data_row.area_rank = int(row['Area Size Rank 1=Highest'])
    data_row.population_density = decimal.Decimal(row['Density people per Sq. Km'])
    data_row.population_density_rank = int(row['Population Density Rank 1=Highest'])

    try:
        data_row.registered_voters_total = int(row['Total Registered Voters'])
        data_row.registered_voters_proportion = decimal.Decimal(row['Registered Voters as % of Population'])
        data_row.registered_voters_proportion_rank = int(row['Registered Voters % Rank 1=Highest'])
        data_row.youth_voters_proportion = decimal.Decimal(row['Youth Voters as a % of Total'])
        data_row.youth_voters_proportion_rank = int(row['Youth Voters % Rank 1=Highest'])
    except KeyError:
        # One some kinds of place, such as Counties, these columns don't exist.
        pass

    data_row.save()
