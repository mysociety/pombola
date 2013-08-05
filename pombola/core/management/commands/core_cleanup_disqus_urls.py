# This script is used to cleanup the URLs that disqus has comments associated.
# Annoyingly Disqus does not appear to strip out commonly added parameters such
# as `gclid` (the Google Click Identifier that AdWords adds to URLs).
#
# Leaving aside that though - when the default page layout changed from tab
# based to individual pages the URLs to the comments all changed, and we started
# to use the disqus_identifier properly. So the URLs would have needed changing
# anyway.
#
# This script takes a CSV file that can be requested on this page:
#
#    http://YOUR_SHORTNAME.disqus.com/admin/tools/migrate/
#    ( click on 'Start URL Mapper' and then on 'you can download a CSV here')
#
# It the outputs (to STDOUT) a CSV that can be uploaded (ie rows with "old_url,
# new_url").
#
# It does the following:
#
#  * Strips off all query parameters
#  * adds '/comments' to the end if needed
#
#  No checking or correcting of the URLs occurs.
#
# The resulting CSV can then be uploaded on the 'URL Mapper' page that the input
# CSV was downloaded from.

import re
import sys
import csv
from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = 'Correct URLs that Disqus has for comments'
    args = '<CSV requested from Disqus>'

    def handle_label(self,  filename, **options):

        csv_reader = csv.reader(open(filename, 'rb'))
        csv_writer = csv.writer(sys.stdout)

        for row in csv_reader:
            old_url = row[0]
            new_url = old_url

            # strip query
            new_url = re.sub(r'\?.*$', '', new_url)

            # add '/comment/' if needed
            if not re.search(r'/comments/$', new_url):
                new_url += 'comments/'

            csv_writer.writerow([old_url, new_url])
