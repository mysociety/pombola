import settings

from django.utils import unittest
from core         import models

from django_date_extensions.fields import ApproximateDate

class PositionTestCase(unittest.TestCase):
    def setUp(self):
        self.person       = models.Person.objects.create(first_name="Bob", last_name="Smith", slug="bob-smith")

        organisation_kind = models.OrganisationKind.objects.create(
            name        = "Test Org",
            name_plural = "Test Orgs",
            slug        = "test-org",
        )
        self.organisation = models.Organisation.objects.create(
            slug = "org",
            name = "The Org",
            kind = organisation_kind,
        )

        place_kind = models.PlaceKind.objects.create(
            name       = "Test Place",
            name_plural= "Test Places",
            slug       = "test-place",
        )

        self.place = models.Place.objects.create(
            name = "The Place",
            slug = "place",
            kind = place_kind,
        )

    def getPos(self, **kwargs):
        title_kind, created = models.PositionTitle.objects.get_or_create(
            name        = 'Job Title',
            name_plural = 'Job Titles',
            slug        = 'job-title',
        )
        return models.Position.objects.create(
            person       = kwargs.get('person',       self.person       ),
            organisation = kwargs.get('organisation', self.organisation ),
            place        = kwargs.get('place',        self.place        ),
            title        = title_kind,
        )

    def testDisplayDates(self):
        
        # get the test dates
        start_date      = ApproximateDate(year=2000, month=01, day=01)
        future_end_date = ApproximateDate(year=2100, month=01, day=01)
        past_end_date   = ApproximateDate(year=2000, month=01, day=02)
        future          = ApproximateDate(future=True)
        

        # load the object
        pos = self.getPos()
        self.assertTrue( pos )

        # check that by default both dates are empty
        self.assertEqual( pos.display_start_date(), '?' )
        self.assertEqual( pos.display_end_date(),   '?' )

        # mark the end_date as future
        pos.end_date = future
        pos.save()
        self.assertEqual( pos.display_start_date(), '?' )
        self.assertEqual( pos.display_end_date(),   'future' )
        self.assertTrue( pos.is_ongoing() )
        
        # give the position some dates (still ongoing)
        pos.start_date = start_date
        pos.end_date   = future_end_date # far in future
        pos.save()
        self.assertEqual( pos.display_start_date(), '1st January 2000' )
        self.assertEqual( pos.display_end_date(),   '1st January 2100' )
        self.assertTrue( pos.is_ongoing() )
        
        # set end date in the past
        pos.end_date = past_end_date
        pos.save()
        self.assertEqual( pos.display_start_date(), '1st January 2000' )
        self.assertEqual( pos.display_end_date(),   '2nd January 2000' )
        self.assertFalse( pos.is_ongoing() )
