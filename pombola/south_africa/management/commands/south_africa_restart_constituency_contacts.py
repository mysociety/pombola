from datetime import date
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django_date_extensions.fields import ApproximateDate

from pombola.core.models import PositionTitle

# A few days before the election:
date_for_last_active_check = date(2014, 5, 1)
# The date of the final results being announced:
date_to_start_new_positions = date(2014, 5, 10)

class Command(NoArgsCommand):
    """Restart constituency contact positions for re-elected MPs and MPLs"""

    help = 'Restart constituency contact positions for re-elected MPs and MPLs'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle_noargs(self, **options):

        pt = PositionTitle.objects.get(name='Constituency Contact')

        for old_position in pt.position_set.all(). \
            currently_active(date_for_last_active_check):

            person = old_position.person

            print "Considering", old_position

            active_positions = person.position_set.all().currently_active()

            # Are they currently an MP or an MPL?
            na_memberships = active_positions.filter(
                organisation__slug='national-assembly',
                title__slug='member')

            # FIXME: Why are there two representations of MPLs?

            pl_memberships = active_positions.filter(
                title__slug='member',
                organisation__kind__slug='provincial-legislature')

            pl_memberships2 = active_positions.filter(
                title__slug='member-of-the-provincial-legislature')

            restart = False

            if na_memberships:
                print "  Restarting because", person, "is currently a Member of the National Assembly"
                restart = True

            if pl_memberships or pl_memberships2:
                print "  Restarting because", person, "is currently a Member of a Provincial Legislature"
                restart = True

            if restart:
                # Set the primary key to None so that when we save it,
                # that creates a new row:
                old_position.pk = None
                old_position.start_date = ApproximateDate(
                    *date_to_start_new_positions.timetuple()[0:3]
                )
                old_position.end_date = ApproximateDate(future=True)

                if options['commit']:
                    print "  Saving the new position"
                    old_position.save()
                else:
                    print "  Not saving the new position (--commit not specified)"
