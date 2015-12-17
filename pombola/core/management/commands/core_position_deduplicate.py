from optparse import make_option

from django.core.management.base import BaseCommand

from pombola.core import models


class Command(BaseCommand):
    help = 'Deduplicate the position entries'

    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete found duplicates'),
        )

    fields_to_order = ('person', 'organisation', 'place', 'title')
    fields_to_compare = fields_to_order + ('subtitle', 'start_date', 'end_date', 'note')

    def handle(self, **options):
        """Go through all the positions and remove any that are duplicates"""

        # get all positions ordered such that duplicates are sequential
        position_qs = models.Position.objects.all().order_by(*self.fields_to_compare)
        previous = None

        for current in position_qs:

            # print "looking at %s" % position
            if previous and self.are_positions_equal(previous, current):

                print "###### Found Matches #################################"
                self.pprint_position(previous)
                self.pprint_position(current)
                print

                if options['delete']:
                    previous.delete()

            previous = current

    def are_positions_equal(self, previous, current):
        """Compare two positions, deleting one if they are the same"""

        # check the fields - if any are different return
        for key in self.fields_to_compare:

            # get the values. Use repr so that future dates compare as equal
            p_val = repr(getattr(previous, key))
            c_val = repr(getattr(current, key))

            if p_val != c_val:
                return False

        return True


    def pprint_position(self, position):
        print "%u: %s"       % (position.id, position)
        print "    %s"       % (position.subtitle)
        print "    %s to %s" % (position.start_date, position.end_date)
