#!/usr/bin/env python

import sys
import re
import csv
import os
import pprint

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../../..'
    )
)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../../../..'
    )
)

from django.utils.text import slugify

from pombola.core import models

def process(filename):
    reader = csv.DictReader(open(filename, 'r'))

    for row in reader:
        pprint.pprint(row)

        # find the person
        person = models.Person.objects.get(slug=row['slug'])

        # create the title
        title, created = models.PositionTitle.objects.get_or_create(slug=slugify(row['title']), defaults=dict(name=row['title']))

        if row.get('organisation'):
            kind, created = models.OrganisationKind.objects.get_or_create(name="Political", defaults={'slug':'political'})
            organisation, created = models.Organisation.objects.get_or_create(
                slug = slugify(row['organisation']),
                defaults = {"kind": kind, 'name': row.get('organisation')},
            )
        else:
            organisation = None

        if row.get('place'):

            if row['title'] == 'Representative':
                kind_name = 'Constituency'
            elif row['title'] == 'Senator':
                kind_name = 'State'
            else:
                kind_name = 'Other'

            kind, created = models.PlaceKind.objects.get_or_create(name=kind_name, defaults={'slug':slugify(kind_name)})
            place, created = models.Place.objects.get_or_create(slug=slugify(row['place']), defaults={"kind":kind, "name":row.get('place')})
        else:
            place = None

        # fiddle the dates so that they are accepted
        for which_date in ['start_date','end_date']:
            if not row.get(which_date): continue
            row[which_date] = re.sub(r'^(\d{4})$', r'\1-00-00', row[which_date])
            row[which_date] = re.sub(r'^(\d{2})$', r'19\1-00-00', row[which_date])

        # create the position
        position, created = models.Position.objects.get_or_create(
            person = person,
            title = title,
            subtitle = row['subtitle'],
            category = row['type'],
            organisation = organisation,
            place = place,
            start_date = row.get('start_date', None),
            end_date = row.get('end_date', None),
        )


for filename in sys.argv[1:]:
    # print filename
    process(filename)

