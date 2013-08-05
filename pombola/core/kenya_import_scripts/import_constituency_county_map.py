# Takes Paul's Excel file of constituencies to counties and
# imports this into the db.

import sys
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pombola.settings'

import csv

from django.template.defaultfilters import slugify

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../..'
    )
)

sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)

from pombola.core import models

all_constituencies = set([x.slug for x in models.Place.objects.filter(kind__slug='constituency')])

csv_filename = sys.argv[1]
csv_file = open(csv_filename, 'rU')
csv_reader = csv.DictReader(csv_file)

for item in csv_reader:
    county_slug = slugify(item['County'] + ' County')

    try:
        county = models.Place.objects.get(
            slug=county_slug, kind__slug='county')
    except models.Place.DoesNotExist:
        print "Can't find county %s" % county_slug
        break

    constituency_slug = slugify(item['Constituency'])

    try:
        constituency = models.Place.objects.get(
            slug=constituency_slug, kind__slug='constituency')
    except models.Place.DoesNotExist:
        print "Can't find constituency %s" % constituency_slug
        continue

    all_constituencies.remove(constituency_slug)

    constituency.parent_place = county
    constituency.save()

print "%d leftover constituencies" % len(all_constituencies), all_constituencies
