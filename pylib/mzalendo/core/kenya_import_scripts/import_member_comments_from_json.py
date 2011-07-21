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
from django.contrib.comments.models import Comment
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

    comment_content = (old_comment['Subject'] or '') + '\n\n' + (old_comment['Comment'] or '')
    comment_content = re.sub( '^\s+', '', comment_content)
    comment_content = re.sub( '\s+$', '', comment_content)

    comment = Comment(
        content_type = ContentType.objects.get_for_model(member),
        object_pk    = member.id,
        site_id      = site.id,
        user_name    = old_comment['Name'][:50],
        user_email   = old_comment['Email'],
        user_url     = old_comment['Website'],        

        comment         = comment_content,
        submit_date     = old_comment['Date'],
        ip_address      = old_comment['IPAddress'],
    )
    comment.save()

