import random
import datetime

from django.core import exceptions
from django.test import TestCase
from django_date_extensions.fields import ApproximateDate

from pombola.core import models

class PositionTest(TestCase):
    def setUp(self):
        self.person = models.Person(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )
        self.person.save()
        
        self.organisation_kind = models.OrganisationKind(
            name = 'Foo',
            slug = 'foo',
        )
        self.organisation_kind.save()

        self.organisation = models.Organisation(
            name = 'Test Org',
            slug = 'test-org',
            kind = self.organisation_kind,
        )
        self.organisation.save()
        
        self.title = models.PositionTitle.objects.create(
            name = 'Test title',
            slug = 'test-title',
        )

    def tearDown(self):
        self.person.delete()
        self.organisation.delete()
        self.organisation_kind.delete()
        self.title.delete()


    def test_unicode(self):
        """Check that missing attributes don't crash"""
        
        position = models.Position(
            person = self.person,
        )
        self.assertEqual( str(position), 'Test Person (??? at ???)' )

    
    def test_display_dates(self):
        """Check that the date that is displayed is correct"""
        position = models.Position(person = self.person)
        
        # Dates that will be used for testing
        past   = ApproximateDate( past=True )
        y2000  = ApproximateDate( year=2000 )
        y2100  = ApproximateDate( year=2100 )
        future = ApproximateDate( future=True )

        # test grid: start, end, uot
        tests = (
            ( None,   None,   "" ),
            ( None,   past,   "Ended" ),
            ( None,   y2000,  "Ended 2000" ),
            ( None,   y2100,  "Will end 2100" ),
            ( None,   future, "Ongoing" ),

            ( past,   None,   "Started" ),
            ( past,   past,   "Ended" ),
            ( past,   y2000,  "Ended 2000" ),
            ( past,   y2100,  "Will end 2100" ),
            ( past,   future, "Ongoing" ),

            ( y2000,  None,   "Started 2000" ),
            ( y2000,  past,   "Started 2000, now ended" ),
            ( y2000,  y2000,  "2000 &rarr; 2000" ),
            ( y2000,  y2100,  "2000 &rarr; 2100" ),
            ( y2000,  future, "Started 2000" ),

            ( y2100,  None,   "Will start 2100" ),
            ( y2100,  y2100,  "2100 &rarr; 2100" ),
            ( y2100,  future, "Will start 2100" ),

            ( future, None,   "Not started yet" ),
            ( future, future, "Not started yet" ),

            # These are impossible, but we don't validate against them. Best check something
            # sensible is returned. Might need if we ever do a site for Time Lords!
            ( y2100,  past,   "Will start 2100, now ended" ),
            ( y2100,  y2000,  "2100 &rarr; 2000" ), 

            ( future, past,   "Ended" ),
            ( future, y2000,  "Ended 2000" ),
            ( future, y2100,  "Will end 2100" ),
                        
        )
        
        for start_date, end_date, expected in tests:
            position.start_date = start_date
            position.end_date   = end_date
            actual = position.display_dates()
            self.assertEqual(
                actual,
                expected,
                "%s -> %s should be '%s', not '%s'" % (start_date, end_date, expected, actual)
            )
    

    def test_past_end_dates(self):
        """
        Check that the entries can be created with past dates. Issues could
        occur as past dates are before all others, so a past end_date would come
        before a start_date. Should have a special case for this.
        """

        # Dates that will be used for testing
        past   = ApproximateDate( past=True )
        y2000  = ApproximateDate( year=2000 )
        y2100  = ApproximateDate( year=2100 )
        future = ApproximateDate( future=True )

        tests = (
            # [start, end, exception]
            [None,   past, None],
            [past,   past, None],
            [y2000,  past, None],
            [y2100,  past, None],
            [future, past, None],

            # Turns out that there is no validation for start > end. Perhaps there should be..
            # [y2100,  past, exceptions.ValidationError],
            # [future, past, exceptions.ValidationError],
        )
        
        def create_position(**kwargs):
            pos = models.Position(**kwargs)
            pos._set_sorting_dates()
            pos.full_clean() # needed as otherwise no validation occurs. Genius!

        for start_date, end_date, exception in tests:
            kwargs = dict(person=self.person, title=self.title, start_date=start_date, end_date=end_date)
            if exception:
                self.assertRaises(exception, create_position, **kwargs)
            else:
                # Should just work without throwing exception
                create_position(**kwargs)                



    def test_sorting(self):
        """Check that the sorting is as expected"""
        
        position_dates = [
            # start_date, end_date, 
            ( 'future',   'future', ),
            ( 'future',   None,     ),
            ( '2002',     'future', ),
            ( '2001',     'future', ),
            ( 'past',     'future'  ),
            ( None,       'future', ),

            ( 'future',   '2010',   ),
            ( '2010',     None,     ),            
            ( '2002',     '2010',   ),
            ( '2001',     '2010',   ),
            ( 'past',     '2010'    ),
            ( None,       '2010',   ),

            ( 'future',   '2009',   ),
            ( '2009',     None,     ),
            ( '2002',     '2009',   ),
            ( '2001',     '2009',   ),
            ( 'past',     '2009'    ),
            ( None,       '2009',   ),

            ( '2002',     None,     ),
            ( '2001',     None,     ),            

            ( 'future',   'past'    ), # <-- this is nonsensical
            ( '2010',     'past'    ),
            ( '2009',     'past'    ),
            ( 'past',     'past'    ),
            ( None,       'past'    ),
            ( 'past',     None      ),
            ( None,       None,     ),
        ]
        
        # create the positions, store the config in the notes and create a list to compare against
        position_expected_order = []
        positions_to_save = []
        
        def approx_date_from_entry(entry):
            if entry is None:
                return None
            if entry == 'future':
                return ApproximateDate(future=True)
            if entry == 'past':
                return ApproximateDate(past=True)
            return ApproximateDate(year=int(entry))

        for dates in position_dates:
            note = u"%s -> %s" % dates

            start_date = approx_date_from_entry(dates[0])
            end_date   = approx_date_from_entry(dates[1])

            position_expected_order.append( note )
            positions_to_save.append(
                models.Position(
                    start_date= start_date,
                    end_date  = end_date,
                    note      = note,
                    person    = self.person,
                )
            )
        
        # save all the positions, but shuffle them first
        random.shuffle( positions_to_save )
        for position in positions_to_save:
            position.save()

        # get all the positions from db and check that they are sorted correctly
        positions_from_db = self.person.position_set.all()
        position_actual_order = [ p.note for p in positions_from_db ]

        # print
        # print position_actual_order
        # print
        # print position_expected_order
        # print

        self.maxDiff = None
        self.assertEqual( position_expected_order, position_actual_order )

    def test_have_at_least_one_attribute(self):
        """
        Positions must have a person, and at least one more attribute.
        Otherwise they don't mean anything
        """
        
        pos = models.Position(
            person = self.person,            
        )

        # call this manually so that the validation does not get all confused
        # about it
        pos._set_sorting_dates()

        with self.assertRaises(exceptions.ValidationError):
            pos.full_clean()
        
        # If this does not blow up then it is OK
        pos.organisation = self.organisation
        pos.full_clean()
        

    def test_place_is_required(self):
        """
        Some job titles (like an MP) are meaningless if there is no place
        associated with them.
        """

        # create position with no place
        position = models.Position(
            person = self.person,
            title  = self.title,
        )
        position._set_sorting_dates()        
        position.full_clean()
        
        # Change the title to require a place
        self.title.requires_place = True
        with self.assertRaises(exceptions.ValidationError):
            position.full_clean()

        # give the pos a place and check that it now validates
        position.place = models.Place( name='Test Place', slug='test-place')
        position.full_clean()

        # put it back
        self.title.requires_place = False
            

    def test_currently_active(self):
        """Test that the currently active filter warks"""

        now          = datetime.datetime.now()
        earlier      = now - datetime.timedelta( days = 7   )
        much_earlier = now - datetime.timedelta( days = 365 )
        later        = now + datetime.timedelta( days = 7   )
        much_later   = now + datetime.timedelta( days = 365 )
        pos_qs = models.Position.objects.all()        

        # check that there are no positions
        self.assertEqual(
            models.Position.objects.all().currently_active().count(), 0
        )

        # create position which is currently active
        position = models.Position.objects.create(
            person     = self.person,
            title      = self.title,
            start_date = ApproximateDate( year=earlier.year, month=earlier.month, day=earlier.day ),
            end_date   = ApproximateDate( year=later.year,   month=later.month,   day=later.day   ),
        )
        
        # check that we match by default
        self.assertEqual( pos_qs.currently_active().count(), 1 )
        self.assertEqual( pos_qs.currently_inactive().count(), 0 )

        # check valid date ranges
        self.assertEqual( pos_qs.currently_active( earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( now     ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( now     ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( later   ).count(), 0 )

        # check that much earlier or much later don't match
        self.assertEqual( pos_qs.currently_active( much_earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_active( much_later   ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( much_earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_later   ).count(), 1 )
        

        # check future dates
        position.start_date = ApproximateDate( year=earlier.year, month=earlier.month, day=earlier.day )
        position.end_date = ApproximateDate(future=True)
        position.save()

        # check that we match by default
        self.assertEqual( pos_qs.currently_active().count(), 1 )
        self.assertEqual( pos_qs.currently_inactive().count(), 0 )

        # check valid date ranges
        self.assertEqual( pos_qs.currently_active( earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( now     ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( now     ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( later   ).count(), 0 )

        # check that much earlier or much later don't match
        self.assertEqual( pos_qs.currently_active( much_earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_active( much_later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_later   ).count(), 0 )


        # check absent end dates
        position.start_date = ApproximateDate( year=earlier.year, month=earlier.month, day=earlier.day )
        position.end_date = None
        position.save()

        # check that we match by default
        self.assertEqual( pos_qs.currently_active().count(), 1 )
        self.assertEqual( pos_qs.currently_inactive().count(), 0 )

        # check valid date ranges
        self.assertEqual( pos_qs.currently_active( earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( now     ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( now     ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( later   ).count(), 0 )

        # check that much earlier or much later don't match
        self.assertEqual( pos_qs.currently_active( much_earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_active( much_later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_later   ).count(), 0 )



        # check absent start and end dates
        position.start_date = None
        position.end_date = None
        position.save()

        # check that we match by default
        self.assertEqual( pos_qs.currently_active().count(), 1 )
        self.assertEqual( pos_qs.currently_inactive().count(), 0 )

        # check valid date ranges
        self.assertEqual( pos_qs.currently_active( earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( now     ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( now     ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( later   ).count(), 0 )

        # check that much earlier or much later don't match
        self.assertEqual( pos_qs.currently_active( much_earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_active( much_later   ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( much_later   ).count(), 0 )



        # check future start dates
        position.start_date = ApproximateDate(future=1)
        position.end_date = None
        position.save()

        # check that we match by default
        self.assertEqual( pos_qs.currently_active().count(), 0 )
        self.assertEqual( pos_qs.currently_inactive().count(), 1 )

        # check valid date ranges
        self.assertEqual( pos_qs.currently_active( earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_active( now     ).count(), 0 )
        self.assertEqual( pos_qs.currently_active( later   ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( now     ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( later   ).count(), 1 )

        # check that much earlier or much later don't match
        self.assertEqual( pos_qs.currently_active( much_earlier ).count(), 0 )
        self.assertEqual( pos_qs.currently_active( much_later   ).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive( much_earlier ).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive( much_later   ).count(), 1 )



        # check partial dates
        mid_2010 = datetime.date(year=2010, month=6, day=1)
        mid_2011 = datetime.date(year=2011, month=6, day=1)
        mid_2012 = datetime.date(year=2012, month=6, day=1)
        mid_2013 = datetime.date(year=2013, month=6, day=1)

        position.start_date = ApproximateDate(year=2011)
        position.end_date   = ApproximateDate(year=2012)
        position.save()

        # from django.forms.models import model_to_dict
        # from pprint import pprint
        # pprint( model_to_dict( position ) )
                
        self.assertEqual( pos_qs.currently_active(mid_2010).count(), 0 )
        self.assertEqual( pos_qs.currently_active(mid_2011).count(), 1 )
        self.assertEqual( pos_qs.currently_active(mid_2012).count(), 1 )
        self.assertEqual( pos_qs.currently_active(mid_2013).count(), 0 )

        self.assertEqual( pos_qs.currently_inactive(mid_2010).count(), 1 )
        self.assertEqual( pos_qs.currently_inactive(mid_2011).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive(mid_2012).count(), 0 )
        self.assertEqual( pos_qs.currently_inactive(mid_2013).count(), 1 )

