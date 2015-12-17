#!/usr/bin/env python

import os
import sys

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)


from pombola.core import models
from django.contrib.contenttypes.models import ContentType

import mp_contacts


phone_kind   = models.ContactKind.objects.get(slug='phone')
email_kind   = models.ContactKind.objects.get(slug='email')

for row in mp_contacts.entries:
    
    (name, phone, email) = row

    if not (phone or email):
        continue

    # code needs reworking now that the name structure of the database has changed
    matches = models.Person.objects.all().is_politician().name_matches( name )
    
    if matches.count() == 0:
        print "  no match for '%s', '%s', '%s'" % (name, phone, email)
        continue
    if matches.count() > 1:
        print "  several matches for %s" % name
        continue
    
    mp = matches[0]
    
    # print "%s -> %s" % ( name, mp.name )


    content_type = ContentType.objects.get_for_model(mp)

    source = "SUNY Kenya spreadsheet entry for '%s'" % name

    if phone:
        models.Contact.objects.get_or_create(
            content_type=content_type,
            object_id=mp.id,
            value=phone,
            kind=phone_kind,
            defaults = {
                "source":source,
            }
        )

    if email:
        models.Contact.objects.get_or_create(
            content_type=content_type,
            object_id=mp.id,
            value=email,
            kind=email_kind,
            defaults = {
                "source":source,
            }
        )

