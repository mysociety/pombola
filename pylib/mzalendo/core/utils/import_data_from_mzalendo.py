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

mps = simplejson.loads( sys.stdin.read() )

constituency_kind = models.PlaceKind.objects.get(slug="constituency")
party_kind        = models.OrganisationKind.objects.get(slug="party")
mp_job_title      = models.PositionTitle.objects.get(slug="mp")
member_job_title  = models.PositionTitle.objects.get(slug="member")
parliament        = models.Organisation.objects.get(slug="parliament")

for mp in mps:
    pprint( mp )

    constituency, created = models.Place.objects.get_or_create(
        name = mp['constituency'],
        slug = slugify(mp['constituency']),
        kind = constituency_kind,
    )

    party, created = models.Organisation.objects.get_or_create(
        name = mp['party'],
        slug = slugify(mp['party']),
        kind = party_kind,
    )

    person, created = models.Person.objects.get_or_create(
        first_name   = mp['first_name'],
        middle_names = mp['middle_name'],
        last_name    = mp['last_name'],
        slug         = slugify( mp['first_name'] + ' ' + mp['last_name']  ) ,
    )

    party_membership, created = models.Position.objects.get_or_create(
        person       = person,
        title        = member_job_title,
        organisation = party,
    )

    mp_position, created = models.Position.objects.get_or_create(
        person       = person,
        title        = mp_job_title,
        organisation = parliament,
        place        = constituency,
    )
