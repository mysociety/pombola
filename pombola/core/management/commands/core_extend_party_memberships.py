# This command is intended to fix issue 550:
#
#   https://github.com/mysociety/pombola/issues/550
#
#   "As mentioned in #494 there are lots of party membership positions
#    that have an end date of 2012 - meaning that on the site many
#    positions are hidden by default. These party memberships should
#    probably be open ended and could be changed to have end dates of
#    'future'"
#
# This script looks for every person in the database, and takes the
# most recent party membery position with the most recent end_date -
# if that position ends with ApproximateDate(2012), change it to
# ApproximateDate(future=True).

from optparse import make_option

import sys

from django.core.management.base import NoArgsCommand

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Person


class Command(NoArgsCommand):
    help = 'Change party memberships that end in 2012 to end in "future".'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):
        for person in Person.objects.all():
            party_positions = person.position_set.all().filter(title__slug='member').filter(organisation__kind__slug='party')
            if not party_positions:
                continue
            most_recent_party_position = party_positions[0]
            if most_recent_party_position.end_date == ApproximateDate(2012):
                most_recent_party_position.end_date = ApproximateDate(future=True)
                message = "2012 end_date to future for %s" % (most_recent_party_position,)
                if options['commit']:
                    most_recent_party_position.save()
                    print >> sys.stderr, "Changing " + message
                else:
                    print >> sys.stderr, "Not changing " + message + "because --commit wasn't specified"
