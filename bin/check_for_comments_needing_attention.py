#!/usr/bin/env python

import mzalendo.setup_env
import sys

from django.core.mail import mail_managers
from mzalendo.comments2.models import Comment

unmoderated = Comment.objects.in_moderation()
flagged = Comment.objects.flagged()

# count the number in each state
unmoderated_count = unmoderated.count()
flagged_count     = flagged.count()
total_count       = unmoderated_count + flagged_count

# If there are no comments to deal with then exit
if total_count == 0:
    sys.exit()

subject = "Comments require attention - %u unmoderated and %u flagged" % ( unmoderated_count, flagged_count )
message = "Please visit the admin and moderate/review the comments as needed."

# print subject
# print message

mail_managers(subject, message)
