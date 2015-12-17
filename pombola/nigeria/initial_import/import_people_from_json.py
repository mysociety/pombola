#!/usr/bin/env python

import json
import sys
import re
import os
import urllib2

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


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

from django.contrib.contenttypes.models import ContentType

from pombola.core import models
from pombola.images.models import Image

profile_url_kind, created = models.ContactKind.objects.get_or_create(slug='profile_url', name="Profile URL")
email_kind, created       = models.ContactKind.objects.get_or_create(slug='email', name="Email")


def process(filename):
    data = json.loads( open(filename, 'r').read() )
    # pprint.pprint( data )
    print "%s (%s) - %s" % (data['name'], data['slug'], filename)

    slug = data['slug']
    
    try:
        person = models.Person.objects.get(slug=slug)
        return # don't try to update the person        
    except models.Person.DoesNotExist:
        person = models.Person(slug=slug)

    person.legal_name    = data['name']
    person.summary       = data['summary']
    person.date_of_birth = data['date_of_birth']

    person.save()
    
    content_type = ContentType.objects.get_for_model(person)
    
    if data.get('profile_url'):
        models.Contact.objects.get_or_create(
            content_type = content_type,
            object_id    = person.id,
            value        = re.sub('\s', '%20', data['profile_url'] ),
            kind         = profile_url_kind,
        )
    
    if data.get('email'):
        models.Contact.objects.get_or_create(
            content_type = content_type,
            object_id    = person.id,
            value        = data['email'],
            kind         = email_kind,
        )

    # import image
    if data.get('image') and 'img_not_found' not in data['image']:

        image_url = re.sub('\s', '%20', data['image'] );

        photo, created = Image.objects.get_or_create(
            content_type = content_type,
            object_id    = person.id,
            source       = image_url,
        )

        if created:

            print "  Fetching " + image_url
            try:
                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write( urllib2.urlopen(image_url).read() )
                img_temp.flush()
                
                photo.image.save( person.slug, File(img_temp) )
                photo.save()
            except urllib2.HTTPError:
                print "  ...failed!"


for filename in sys.argv[1:]:
    # print filename
    process( filename )

