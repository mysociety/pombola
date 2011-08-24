#!/usr/bin/env python

import os
import sys
import re

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)

import setup_env

import simplejson
from pprint import pprint
from core import models
from django_date_extensions.fields import ApproximateDate
from warnings import warn
from django.template.defaultfilters import slugify

json_filename = '/home/evdb/mzalendo_data/political_and_business_positions.json'

# python 2.6
# with open(json_filename) as json_file:
#     objects = simplejson.loads( json_file.read() )

# python 2.5
objects = simplejson.loads( open(json_filename).read() )

org_lookup   = {}
title_lookup = {}
place_lookup = {}

# objects['titles']        = {}
# objects['organisations'] = {}
# objects['places'] = {}

for key in sorted(objects['organisations'].keys()):
    obj = objects['organisations'][key]
    
    defaults = {}
    defaults['name'] = key

    if obj['kind']:
        # print obj['kind'] 
        defaults['kind'] = models.OrganisationKind.objects.get(name=obj['kind'])
    else:
        defaults['kind'] = models.OrganisationKind.objects.get(name='Unknown') 
        
    org_lookup[ key ], created = models.Organisation.objects.get_or_create(
        slug = obj['slug'],
        defaults = defaults,
    )


for key in sorted(objects['titles'].keys()):
    obj = objects['titles'][key]
    
    defaults = {
        'name': key,
    }

    title_lookup[ key ], created = models.PositionTitle.objects.get_or_create(
        slug = obj['slug'],
        defaults = defaults,
    )

for key in sorted(objects['places'].keys()):
    obj = objects['places'][key]
    
    defaults = {
        'name': key,
        'kind': models.PlaceKind.objects.get(name='Unknown'),
    }

    title_lookup[ key ], created = models.Place.objects.get_or_create(
        slug = obj['slug'],
        defaults = defaults,
    )


for obj in objects['positions']:

    # normalise all whitespace and strip of leading/trailing
    for key in obj:
        obj[key] = re.sub(r'\s+', ' ', obj[key]).strip()

    if not obj['import'] == 'y':
        continue

    # pprint( obj )

    # Load the org
    if obj['organisation']:
        try:
            organisation = org_lookup[obj['organisation']]
        except KeyError:
            objects['organisations'][obj['organisation']] = {
                "slug": slugify( obj['organisation'] ),
                "kind": "",
            }
    else:
        organisation = None
    
    # Load the job title
    if obj['job title']:
        title_name = obj['job title']
        try:
            title = title_lookup[title_name]
        except KeyError:
            objects['titles'][title_name] = {
                "slug": slugify( title_name ),
            }
    else:
        title = None

    # Load the place
    if obj['place']:
        try:
            place = place_lookup[ obj['place'] ]
        except KeyError:
            objects['places'][ obj['place'] ] = {
                "slug": slugify( obj['place'] ),
            }
    else:
        place = None
    
    def tidy_date(date):
        if not date:
            return None
            
        if date == 'future':
            return ApproximateDate(future=True)
        
        if re.match( r'^\d{4}$', date):
            return ApproximateDate(year=int(date))
        
        month_year = re.match( r'^(\d{2})-(\d{4})$', date)
        if month_year:
            month, year = month_year.groups()
            return ApproximateDate(month=int(month), year=int(year))

        print 'bad date: %s' % date
        
    
    start_date = tidy_date( obj['start'])
    end_date   = tidy_date( obj['end'])


    # continue
    
    # Load the person
    person = models.Person.objects.get( original_id=obj['member_id'] )
        
    # create the position
    models.Position(
        person=       person,
        organisation= organisation,
        place=        place,
        title=        title,
        start_date=   start_date,
        end_date=     end_date,
    ).save()



# with open(json_filename, 'w') as json_file:
#     simplejson.dump( objects, json_file, sort_keys=True, indent=4, ensure_ascii=False, )
