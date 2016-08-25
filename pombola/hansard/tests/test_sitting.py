from datetime import date, time

from django.test import TestCase
from pombola.hansard.models import Source, Sitting, Venue
from pombola.hansard.views import get_sittings_from_slugs


class HansardSittingTest(TestCase):

    fixtures = ['hansard_test_data']

    def setUp(self):
        # grab a source from the test_data
        self.source = Source.objects.all()[0]
        self.venue  = Venue.objects.all()[0]

        self.sitting_none = Sitting.objects.get(
            venue__slug='national_assembly',
            start_date='2010-04-11',
            start_time=None)
        self.sitting_morning = Sitting.objects.get(
            venue__slug='national_assembly',
            start_date='2010-04-11',
            start_time='09:30:00')
        self.sitting_afternoon = Sitting.objects.get(
            venue__slug='national_assembly',
            start_date='2010-04-11',
            start_time='14:30:00')


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


    def test_sitting_link_url(self):
        self.assertEqual(
            '/hansard/sitting/national_assembly/2010-04-11',
            self.sitting_none.get_absolute_url())
        self.assertEqual(
            '/hansard/sitting/national_assembly/2010-04-11-09-30-00',
            self.sitting_morning.get_absolute_url())
        self.assertEqual(
            '/hansard/sitting/national_assembly/2010-04-11-14-30-00',
            self.sitting_afternoon.get_absolute_url())

    def test_sitting_url_decoding(self):
        s = get_sittings_from_slugs('national_assembly', '2010-04-11')
        self.assertEqual(1, len(s))
        self.assertEqual(s[0].id, self.sitting_none.id)

        s = get_sittings_from_slugs('national_assembly', '2010-04-11-09-30-00')
        self.assertEqual(1, len(s))
        self.assertEqual(s[0].id, self.sitting_morning.id)

        s = get_sittings_from_slugs('national_assembly', '2010-04-11-14-30-00')
        self.assertEqual(1, len(s))
        self.assertEqual(s[0].id, self.sitting_afternoon.id)
