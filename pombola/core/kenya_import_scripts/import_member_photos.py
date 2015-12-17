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
import time
import urllib

from django.core.files.base import ContentFile
from pombola.core import models
from pombola.images.models import Image


constituency_kind = models.PlaceKind.objects.get(slug="constituency")

objects    = simplejson.loads( sys.stdin.read() )

for obj in objects:
    
    member_id = obj['MemberID']
    image_link = obj["ImageLink"]
    
    if not image_link:
        continue

    try:
        person = models.Person.objects.get(original_id=member_id)
    except models.Person.DoesNotExist:
        print "Could not find %s - ignoring" % person
        continue

    url = 'http://mzalendo.com/Images/%s' % image_link


    source_string = "Original Mzalendo.com website (%s)" % image_link

    # check to see if this photo has already been used
    if Image.objects.filter(source=source_string).count():
        print "Skipping %s - image already used" % person
        continue

    print "Fetching image for '%s': '%s'" % ( person, url )
    person_image = Image(
        content_object = person,
        source = source_string,
    )
    person_image.image.save(
        name    = image_link,
        content = ContentFile( urllib.urlopen( url ).read() ),
    )

    # break
    time.sleep(2)
