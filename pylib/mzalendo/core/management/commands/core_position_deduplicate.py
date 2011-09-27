from optparse import make_option
from pprint import pprint

from django.core.management.base import NoArgsCommand
from django.template.defaultfilters import slugify
from django.conf import settings

from mzalendo.helpers import geocode
from mzalendo.core import models


class Command(NoArgsCommand):
    help = 'Deduplicate the position entries'

    fields_to_compare = ('person', 'organisation', 'place', 'title', 'subtitle', 'start_date', 'end_date' )

    def handle_noargs(self, **options):
        """Go through all the positions and report any that are duplicates"""


        # get all positions ordered such that duplicates are sequential
        position_qs = models.Position.objects.all().order_by( *self.fields_to_compare )
        
        previous_position = None
        
        for position in position_qs:
            # print "looking at %s" % position
            if previous_position:
                self.compare_positions( previous_position, position )

            previous_position = position
            
    def compare_positions(self, previous, current):
        """Compare two positions, deleting one if they are the same"""

        # check the fields - if any are different return
        for key in self.fields_to_compare:
            if getattr(previous, key) != getattr(current, key):
                return None
        
        print "## Potential Matches #################################"
        self.pprint_position( previous )
        self.pprint_position( current )
        
    def pprint_position(self, position):
        print "%s" % position
        print "  %s to %s" % ( position.start_date, position.end_date)
