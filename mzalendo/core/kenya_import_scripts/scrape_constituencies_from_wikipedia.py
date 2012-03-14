import sys
import os
import re

os.environ['DJANGO_SETTINGS_MODULE'] = 'mzalendo.settings'

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

import itertools
from BeautifulSoup import BeautifulSoup

from django.template.defaultfilters import slugify

from mzalendo.core import models


# Can't download this with urllib2 as wikipedia won't let us,
# So there is a wgeted version sitting in this directory.
# source_url = 'http://en.wikipedia.org/wiki/List_of_constituencies_of_Kenya'

output_dict = {}

source_html = open('List_of_constituencies_of_Kenya')
soup = BeautifulSoup(source_html)

district_constituency_lists = soup.findAll('ul')

assert len(district_constituency_lists) == 47, len(district_constituency_lists)

for constituency_list in district_constituency_lists:
    try:
        province_name = constituency_list.findPrevious('h3').find('span', {'class': 'mw-headline'}).a.string
    except AttributeError:
        # On wikipedia, there is no separate province listing for Nairobi.
        province_name = 'Nairobi'

    province_slug = slugify(province_name)# + '-province'

    try:
        models.Place.objects.get(slug=province_slug, kind__slug='province')
    except models.Place.DoesNotExist:
        try: 
            models.Place.objects.get(slug=province_slug + '-province', kind__slug='province')
        except models.Place.DoesNotExist:
            print "Can't find province: %s" % province_slug
            continue

    try:
        district_name = constituency_list.findPrevious('p').a.string
    except AttributeError:
        # District is also done differently for Nairobi.
        district_name = 'Nairobi County'

    district_name = re.sub(r' District$', ' County', district_name)
    district_slug = slugify(district_name)

    try:
        models.Place.objects.get(slug=district_slug , kind__slug='county')
    except models.Place.DoesNotExist:
        print "Can't find district: %s" % district_slug
        continue

    province_dict = output_dict.setdefault(province_slug, {})
    district_list = province_dict.setdefault(district_slug, [])

    constituencies = constituency_list.findAll('li')

    for constituency in constituencies:
        constituency_name = constituency.a.string
        constituency_name = re.sub(r' Constituency$', r'', constituency_name) 
        constituency_slug = slugify(constituency_name)
            
    try:
        models.Place.objects.get(slug=constituency_slug, kind__slug='constituency')
    except models.Place.DoesNotExist:
        print "Can't find constituency: %s" % constituency_slug
        continue

        district_list.append(constituency_slug)

    district_list.sort()

import pdb;pdb.set_trace()
