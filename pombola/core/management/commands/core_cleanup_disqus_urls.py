# This script is used to cleanup the URLs that disqus has comments associated.
# Annoyingly Disqus does not appear to strip out commonly added parameters such
# as `gclid` (the Google Click Identifier that AdWords adds to URLs), and we've
# got separate threads for each sub-page of a person, whereas they should
# really just be a single thread.
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
#  * Identifies the type of the object (person, place or organisation) and
#    its slug (even if it's in a percent-encoded query parameter from a proxy)
#  * Reconstructs the canonical URL for that object
#
# This doesn't actually check that the URL works, but attempts to
# remove anything extraneous to produce the canonical URL for the
# person.
#
# The resulting CSV can then be uploaded on the 'URL Mapper' page that the input
# CSV was downloaded from.

from __future__ import unicode_literals, print_function

import re
import sys
import csv
from urllib import unquote
from urlparse import urlsplit
from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = 'Correct URLs that Disqus has for comments'
    args = '<CSV requested from Disqus>'

    def rewrite_url(self, old_url):
        split_url = urlsplit(old_url)
        path_re = r'/+(hansard/+)?(?P<type>person|place|organisation)/+([^/?]*?)(/| |$)'
        if split_url.netloc == 'info.mzalendo.com':
            # Look for the straightforward pattern of person, organisation
            # or place page or sub-pages:
            m = re.search('^' + path_re, split_url.path)
        else:
            # Otherwise it's probably a proxy URL, in which case we
            # can sometimes find the path by removing the
            # percent-encoding from it:
            unquoted = unquote(old_url)
            m = re.search(path_re, unquoted)
        if m:
            return 'http://info.mzalendo.com/{1}/{2}/'.format(*m.groups())

    def handle_label(self,  filename, **options):
        verbose = options['verbosity'] > 1

        new_mapping = []

        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                old_url = row[0]
                new_url = self.rewrite_url(old_url)
                if new_url is None:
                    if verbose:
                        print("Skipping: {0}".format(old_url), file=sys.stderr)
                else:
                    new_mapping.append([old_url, new_url])

        writer = csv.writer(sys.stdout)
        for old, new in new_mapping:
            if old != new:
                writer.writerow([old, new])
