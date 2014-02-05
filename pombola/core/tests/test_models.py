from django.utils import unittest
from django.test.utils import override_settings
from django_date_extensions.fields import ApproximateDate
from django.contrib.contenttypes.models import ContentType

from pombola.core import models
from pombola.tasks.models import Task

class PositionTestCase(unittest.TestCase):
    def setUp(self):
        self.person       = models.Person.objects.create(legal_name="Bob Smith", slug="bob-smith")

        organisation_kind = models.OrganisationKind.objects.create(
            name        = "Test Org",
            slug        = "test-org",
        )
        self.organisation = models.Organisation.objects.create(
            slug = "org",
            name = "The Org",
            kind = organisation_kind,
        )

        place_kind = models.PlaceKind.objects.create(
            name       = "Test Place",
            slug       = "test-place",
        )

        self.place = models.Place.objects.create(
            name = "The Place",
            slug = "place",
            kind = place_kind,
        )

        self.position_title = models.PositionTitle.objects.create(
            name        = 'Job Title',
            slug        = 'job-title',
        )

    def tearDown(self):
        """Clean up after the tests"""
        self.person.delete()
        self.organisation.delete()
        self.place.delete()
        self.position_title.delete()

    def getPos(self, **kwargs):
        return models.Position.objects.create(
            person       = kwargs.get('person',       self.person       ),
            organisation = kwargs.get('organisation', self.organisation ),
            place        = kwargs.get('place',        self.place        ),
            title        = self.position_title,
            start_date   = '',
            end_date     = '',
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


class PersonAndContactTasksTest( unittest.TestCase ):
    def setUp(self):
        pass

    def test_missing_contacts(self):
        person = models.Person(
            legal_name = "Test Person",
            slug       = 'test-person'
        )
        person.save()

        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for(person) ],
            ['find-missing-phone', 'find-missing-email', 'find-missing-address'],
        )

        # add a phone number and check that the tasks get updated
        phone = models.ContactKind(
            slug='phone', name='Phone',
        )
        phone.save()

        contact = models.Contact(
            content_type = ContentType.objects.get_for_model(person),
            object_id    = person.id,
            kind         = phone,
            value        = '07891 234 567',
        )
        contact.save()

        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for(person) ],
            ['find-missing-email', 'find-missing-address'],
        )

        person.delete()


class PersonNamesTest( unittest.TestCase ):

    def setUp(self):
        self.person, _ = models.Person.objects.get_or_create(
            legal_name = "John Smith",
            slug = "john-smith")
        self.person.add_alternative_name("John Q. Public", name_to_use=True)
        self.person.add_alternative_name("John Doe", name_to_use=False)

    def test_alternative_names(self):
        self.assertEqual(self.person.name, "John Q. Public")

        self.assertEqual(set(self.person.additional_names(include_name_to_use=True)),
                         set(("John Q. Public", "John Doe")))

        self.assertEqual(self.person.all_names_set(),
                         set(("John Q. Public", "John Doe", "John Smith")))

    def tearDown(self):
        self.person.delete()


class PersonPlaceTest(unittest.TestCase):

    def setUp(self):
        # Make a person, with some positions, titles and some places to be
        # associated with them.
        self.person = models.Person.objects.create(
            legal_name="Test Person",
            slug='test-person'
        )

        self.organisation_kind = models.OrganisationKind.objects.create(
            name = "Test Org",
            slug = "test-org",
        )
        self.organisation = models.Organisation.objects.create(
            slug = "org",
            name = "The Org",
            kind = self.organisation_kind,
        )

        self.place_kind = models.PlaceKind.objects.create(
            name = "Test Place",
            slug = "test-place",
        )
        self.place_a = models.Place.objects.create(
            name = "The Place",
            slug = "place",
            kind = self.place_kind,
        )
        self.place_b = models.Place.objects.create(
            name = "The Other Place",
            slug = "other-place",
            kind = self.place_kind,
        )
        self.place_c = models.Place.objects.create(
            name = "The Third Place",
            slug = "third-place",
            kind = self.place_kind,
        )
        self.place_d = models.Place.objects.create(
            name = "The Third Place",
            slug = "fourth-place",
            kind = self.place_kind,
        )

        self.position_title_a = models.PositionTitle.objects.create(
            name = 'Job Title',
            slug = 'job-title',
        )
        self.position_title_b = models.PositionTitle.objects.create(
            name = 'Other Job Title',
            slug = 'other-job-title',
        )
        self.position_title_c = models.PositionTitle.objects.create(
            name = 'Third Job Title',
            slug = 'third-job-title',
        )

        # Create positions held by the same person at all the different places

        # "Job Title"
        self.position_a = models.Position.objects.create(
            person = self.person,
            organisation = self.organisation,
            place = self.place_a,
            title = self.position_title_a,
            start_date = '',
            end_date = '',
            category = 'political',
        )
        self.position_b = models.Position.objects.create(
            person = self.person,
            organisation = self.organisation,
            place = self.place_d,
            title = self.position_title_b,
            start_date = '',
            end_date = '',
            category = 'education', # Not political, to test choice of positions
        )

        # "Other Job Title"
        self.position_c = models.Position.objects.create(
            person = self.person,
            organisation = self.organisation,
            place = self.place_a,
            title = self.position_title_b,
            start_date = '',
            end_date = '',
            category = 'political',
        )
        self.position_d = models.Position.objects.create(
            person = self.person,
            organisation = self.organisation,
            place = self.place_b,
            title = self.position_title_b,
            start_date = '',
            end_date = '',
            category = 'political',
        )

        # "Third Job Title"
        self.position_e = models.Position.objects.create(
            person = self.person,
            organisation = self.organisation,
            place = self.place_c,
            title = self.position_title_c,
            start_date = '',
            end_date = '',
            category = 'political',
        )

    def tearDown(self):
        self.person.delete()
        self.organisation.delete()
        self.organisation_kind.delete()
        self.place_a.delete()
        self.place_b.delete()
        self.place_c.delete()
        self.place_kind.delete()
        self.position_title_a.delete()
        self.position_title_b.delete()
        self.position_title_c.delete()
        self.position_a.delete()
        self.position_b.delete()
        self.position_c.delete()
        self.position_d.delete()
        self.position_e.delete()

    def test_constituencies_are_distinct(self):
        self.assertEqual(len(self.person.constituencies()), 3)
        self.assertTrue(self.place_a in self.person.constituencies())
        self.assertTrue(self.place_b in self.person.constituencies())
        self.assertTrue(self.place_c in self.person.constituencies())

    def test_constituencies_comes_from_political_positions(self):
        self.assertTrue(self.place_d not in self.person.constituencies())



class SummaryTest( unittest.TestCase ):
    def setUp(self):
        pass

    def test_empty_summary_is_false(self):
        person, created = models.Person.objects.get_or_create(
            legal_name = "Test Person",
            slug       = 'test-person'
        )
        person.save()

        # An empty markitup field should be false and have no length so that in
        # the templates its truthiness is correct.
        self.assertFalse( person.summary )
        self.assertEqual( len(person.summary), 0 )


class RelatedOrganisationTest(unittest.TestCase):
    def test_creation(self):
        """Check that it's possible to relate organisations

        For the moment, this just checks that it's possible to create
        a OrganisationRelation and OrganisationRelationKind."""

        party_kind = models.OrganisationKind.objects.create(name='Party',
                                                            slug='party')
        party_office_kind = models.OrganisationKind.objects.create(name='Party Office',
                                                                   slug='party-office')

        party = models.Organisation.objects.create(name='The Imaginary Party',
                                                   slug='imaginary',
                                                   kind=party_kind)

        office = models.Organisation.objects.create(name='Local Office',
                                                    slug='local-office',
                                                    kind=party_office_kind)

        rel_kind = models.OrganisationRelationshipKind.objects.create(
            name='has_office')

        rel = models.OrganisationRelationship.objects.create(
            organisation_a=office,
            organisation_b=party,
            kind=rel_kind)
