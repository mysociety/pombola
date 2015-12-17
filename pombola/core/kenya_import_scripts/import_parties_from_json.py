#!/usr/bin/env python

import os
import sys

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)



import simplejson
from pprint import pprint

from django.utils.text import slugify

from django_date_extensions.fields import ApproximateDate

from pombola.core import models


party_kind = models.OrganisationKind.objects.get(slug="party")
parties = simplejson.loads(sys.stdin.read())

for party in parties:
    pprint(party)

    try:
        org = models.Organisation.objects.get(
            slug = slugify(party['Acronym'])
        )
    except models.Organisation.DoesNotExist:
        org = models.Organisation(
            slug = slugify(party['Acronym'])
        )

    org.kind = party_kind
    org.original_id = party['PartyID']
    org.name = party['Name']

    if party.get('FoundationYear'):
        org.started = ApproximateDate(year=int(party['FoundationYear']))

    org.save()
