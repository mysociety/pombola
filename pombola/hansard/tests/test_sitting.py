import os
import datetime

from datetime import date, time

from django.test import TestCase
from hansard.models import Source, Sitting, Venue

class HansardSittingTest(TestCase):

    fixtures = ['hansard_test_data']

    def setUp(self):
        # grab a source from the test_data
        self.source = Source.objects.all()[0]
        self.venue  = Venue.objects.all()[0]


    def test_sitting_naming(self):
        """Check that the name is correct for the various permutations"""

        sitting = Sitting(
            source     = self.source,
            venue      = self.venue,
            start_date = date( 2011, 11, 15 ),
        )

        self.assertEqual( str(sitting), 'National Assembly 2011-11-15' )

        sitting.end_date = date( 2011, 11, 15 )
        self.assertEqual( str(sitting), 'National Assembly 2011-11-15' )

        sitting.end_date = date( 2011, 11, 16 )
        self.assertEqual( str(sitting), 'National Assembly 2011-11-15 to 2011-11-16' )

        sitting.start_time = time( 13, 0 )
        self.assertEqual( str(sitting), 'National Assembly 2011-11-15 13:00 to 2011-11-16' )

        sitting.end_date = date( 2011, 11, 15 )
        self.assertEqual( str(sitting), 'National Assembly 2011-11-15: 13:00' )

        sitting.end_time = time( 18, 0 )
        self.assertEqual( str(sitting), 'National Assembly 2011-11-15: 13:00 to 18:00' )
        
        sitting.end_date = date( 2011, 11, 16 )
        self.assertEqual( str(sitting), 'National Assembly 2011-11-15 13:00 to 2011-11-16 18:00' )