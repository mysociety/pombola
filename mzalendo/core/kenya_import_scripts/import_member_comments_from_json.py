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
from core.models import Person

from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from mz_comments import CommentWithTitle
from django.contrib.sites.models import Site

comments = simplejson.loads( sys.stdin.read() )

site = Site.objects.all()[0]

for old_comment in comments:
    pprint( old_comment )

    try:
        member = Person.objects.get(original_id=old_comment['MemberID'])
    except Person.DoesNotExist:
        print "'%s' not found in db" % old_comment['MemberID']
        continue

    comment_title   = old_comment['Subject'] or ''
    comment_content = old_comment['Comment'] or ''

    comment = CommentWithTitle(
        content_type = ContentType.objects.get_for_model(member),
        object_pk    = member.id,
        site_id      = site.id,
        user_name    = old_comment['Name'][:50],
        user_email   = old_comment['Email'],
        user_url     = old_comment['Website'],        

        title           = comment_title.strip(),
        comment         = comment_content.strip(),
        submit_date     = old_comment['Date'],
        ip_address      = old_comment['IPAddress'],
    )
    comment.save()

