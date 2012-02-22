# Takes Paul's Excel file of constituencies to counties and
# imports this into the db.

import sys
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'mzalendo.settings'

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

from mzalendo.core import models

all_constituencies = set([x.slug for x in models.Place.objects.filter(kind__slug='constituency')])

csv_filename = sys.argv[1]
csv_file = open(csv_filename)
csv_reader = csv.reader(csv_file)

# First line is just headers
csv_reader.next()

county_name = None
county_slug = None
constituency_slug = None

for county_text, constituency_name, count in csv_reader:
    if not constituency_name:
        continue

    if county_text:
        county_name = county_text
        county_slug = slugify(county_name) + '-county'

        try:
            county = models.Place.objects.get(
                slug=county_slug, kind__slug='county')
        except models.Place.DoesNotExist:
            print "Can't find county %s" % county_slug
            break

    constituency_slug = slugify(constituency_name)

    try:
        constituency = models.Place.objects.get(
            slug=constituency_slug, kind__slug='constituency')
    except models.Place.DoesNotExist:
        print "Can't find constituency %s" % constituency_slug
        continue

    all_constituencies.remove(constituency_slug)

    constituency.parent_place = county
    constituency.save()

print "Left over constituencies", all_constituencies
