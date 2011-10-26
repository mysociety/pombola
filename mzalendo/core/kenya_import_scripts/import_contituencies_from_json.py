#!/usr/bin/env python

import os
import sys

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)

import setup_env

import simplejson
from pprint import pprint
from django.template.defaultfilters import slugify
from core import models
from django_date_extensions.fields import ApproximateDateField, ApproximateDate

constituency_kind = models.PlaceKind.objects.get(slug="constituency")
objects    = simplejson.loads( sys.stdin.read() )

for obj in objects:
    pprint( obj )

    # {'Code': '001',
    #  'ConstituencyID': '1',
    #  'DistrictID': '86',
    #  'MemberID': '19',
    #  'Name': 'Makadara',
    #  'Population': '0',
    #  'RegisteredVoters': '132630'}
         
    try:
        db_obj = models.Place.objects.get(
            slug = slugify(obj['Name'])
        )
    except models.Place.DoesNotExist:
        db_obj = models.Place(
            slug = slugify(obj['Name'])
        )
        
    db_obj.kind        = constituency_kind  
    db_obj.original_id = obj['ConstituencyID']
    db_obj.name        = obj['Name']

    db_obj.save()

