#!/usr/bin/env python

import os
import sys

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '/../..'
    )
)



import simplejson
from pprint import pprint
from pombola.core.models import Person

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.text import slugify

from comments2.models import Comment


comments = simplejson.loads( sys.stdin.read() )

for old_comment in comments:
    pprint( old_comment )

    try:
        member = Person.objects.get(original_id=old_comment['MemberID'])
    except Person.DoesNotExist:
        print "'%s' not found in db" % old_comment['MemberID']
        continue

    comment_title   = old_comment['Subject'] or ''
    comment_content = old_comment['Comment'] or ''

    username = slugify(old_comment['Name'][:30])

    try:
        user = User.objects.get(email=old_comment['Email'])
    except User.DoesNotExist:

        counter = 0

        while True:
            suffix = str( counter or '')
            length = 30 - len(suffix)
            trial_username = username[:length] + suffix
            if User.objects.filter(username=trial_username).count() == 0:
                break
            counter += 1

        names = old_comment['Name'].split(None, 1)
        first_name = names[0]
        if len(names) > 1:
            last_name = names[1]
        else:
            last_name = ''

        user = User(
            username   = trial_username,
            first_name = first_name[:30],
            last_name  = last_name[:30],
            email      =  old_comment['Email'],
            password   = '',
        )
        user.set_unusable_password()
        user.save()

    comment = Comment(
        content_type = ContentType.objects.get_for_model(member),
        object_id    = member.id,
        user         = user,

        status       = 'approved',
        title        = comment_title.strip(),
        comment      = comment_content.strip(),
        submit_date  = old_comment['Date'],
        ip_address   = old_comment['IPAddress'],
    )
    comment.save()

