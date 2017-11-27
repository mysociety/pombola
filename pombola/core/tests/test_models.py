from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django_date_extensions.fields import ApproximateDate
from django.contrib.contenttypes.models import ContentType

from slug_helpers.models import SlugRedirect

from pombola.core import models
from pombola.tasks.models import Task


class PositionTestCase(TestCase):
    def setUp(self):
        self.person       = models.Person.objects.create(legal_name="Bob Smith", slug="bob-smith")

        self.organisation_kind = models.OrganisationKind.objects.create(
            name        = "Test Org",
            slug        = "test-org",
        )
        self.organisation = models.Organisation.objects.create(
            slug = "org",
            name = "The Org",
            kind = self.organisation_kind,
        )

        self.place_kind = models.PlaceKind.objects.create(
            name       = "Test Place",
            slug       = "test-place",
        )

        self.place = models.Place.objects.create(
            name = "The Place",
            slug = "place",
            kind = self.place_kind,
        )

        self.position_title = models.PositionTitle.objects.create(
            name        = 'Job Title',
            slug        = 'job-title',
        )

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


class PositionCurrencyTest(TestCase):

    def setUp(self):
        self.person = models.Person.objects.create(
            legal_name='Test Person',
            slug='test-person'
        )
        self.organisation_kind = models.OrganisationKind.objects.create(
            name="Test Org Kind",
            slug="test-org-kind",
        )
        self.organisation = models.Organisation.objects.create(
            name='Test Organisation',
            slug='test-organistion',
            kind=self.organisation_kind,
        )

    def test_from_past_still_current(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(year=2200, month=1, day=1),
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([position], list(current_positions))

    def test_from_blank_past_still_current(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date='',
            end_date=ApproximateDate(year=2200, month=1, day=1),
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([position], list(current_positions))

    def test_from_past_not_current(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(year=2010, month=1, day=1)
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([], list(current_positions))

    def test_from_blank_past_not_current(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date='',
            end_date=ApproximateDate(year=2010, month=1, day=1)
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([], list(current_positions))

    def test_from_recent_to_future(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2001, month=4, day=1),
            end_date=ApproximateDate(future=True)
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([position], list(current_positions))

    def test_from_recent_to_blank_future(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2001, month=4, day=1),
            end_date=''
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([position], list(current_positions))

    def test_from_soon_to_future(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2050, month=12, day=25),
            end_date=ApproximateDate(future=True)
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([], list(current_positions))

    def test_from_soon_to_blank_future(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2050, month=12, day=25),
            end_date=''
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([], list(current_positions))

    def test_short_recent_past(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2010, month=7, day=1),
            end_date=ApproximateDate(year=2010, month=12, day=31),
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([], list(current_positions))

    def test_short_near_future(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2050, month=1, day=1),
            end_date=ApproximateDate(year=2050, month=6, day=30),
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([], list(current_positions))

    def test_normal_current(self):
        position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            start_date=ApproximateDate(year=2000, month=1, day=1),
            end_date=ApproximateDate(year=2100, month=12, day=31),
        )
        current_positions = models.Position.objects.all().currently_active()
        self.assertEqual([position], list(current_positions))


class PersonGetSlugOrIdTest(TestCase):
    def setUp(self):
        self.person = models.Person(
            legal_name = "Test Person",
            slug       = 'test-person'
        )
        self.person.save()

    def tearDown(self):
        self.person.delete()

    def test_get_with_id(self):
        result = models.Person.objects.get_by_slug_or_id(self.person.id)
        self.assertEqual(result.id, self.person.id)

    def test_get_with_slug(self):
        result = models.Person.objects.get_by_slug_or_id(self.person.slug)
        self.assertEqual(result.id, self.person.id)

    def test_id_not_found(self):
        temp_person = models.Person.objects.create(
            legal_name = 'Temp Person'
        )
        person_id = temp_person.id
        temp_person.delete()
        with self.assertRaises(models.Person.DoesNotExist):
            models.Person.objects.get_by_slug_or_id(person_id)

    def test_slug_not_found(self):
        with self.assertRaises(models.Person.DoesNotExist):
            models.Person.objects.get_by_slug_or_id('not-in-db')


class PersonAndContactTasksTest(TestCase):
    def setUp(self):
        self.person = models.Person(
            legal_name = "Test Person",
            slug       = 'test-person'
        )
        self.person.save()
        self.phone = models.ContactKind(
            slug='phone', name='Phone',
        )
        self.phone.save()

    def test_missing_contacts(self):

        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for(self.person) ],
            ['find-missing-phone', 'find-missing-email', 'find-missing-address'],
        )

        # add a phone number and check that the tasks get updated

        contact = models.Contact(
            content_type = ContentType.objects.get_for_model(self.person),
            object_id    = self.person.id,
            kind         = self.phone,
            value        = '07891 234 567',
        )
        contact.save()

        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for(self.person) ],
            ['find-missing-email', 'find-missing-address'],
        )


class PersonNamesTest(TestCase):

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


class PersonRedirectUniquenessTest(TestCase):

    def test_redirect_uniqueness_validation(self):
        # Validation should stop someone changing a person slug to one
        # that's redirecting via SlugRedirect.
        redirectee = models.Person.objects.create(
            legal_name='Johan Sebastian Bach',
            slug='bach',
        )
        existing_redirect = SlugRedirect.objects.create(
            new_object=redirectee,
            old_object_slug='jsb',
        )
        other_person = models.Person(
            legal_name='John Smith Bloggs',
            slug='jsb'
        )
        with self.assertRaises(ValidationError):
            other_person.clean_fields()


class PlaceRedirectUniquenessTest(TestCase):

    def test_redirect_uniqueness_validation(self):
        # Validation should stop someone changing a place slug to one
        # that's redirecting via SlugRedirect.
        pkind = models.PlaceKind.objects.create(
            name="Example Places",
            slug="example-places",
        )
        place_redirected_to = models.Place.objects.create(
            name='Echo Beach',
            slug='echo-beach',
            kind=pkind,
        )
        existing_redirect = SlugRedirect.objects.create(
            new_object=place_redirected_to,
            old_object_slug='eb',
        )
        other_place = models.Place(
            name='Ethereal Boulevard',
            slug='eb',
            kind=pkind,
        )
        with self.assertRaises(ValidationError):
            other_place.clean_fields()


class OrganisationRedirectUniquenessTest(TestCase):

    def test_redirect_uniqueness_validation(self):
        # Validation should stop someone changing an organisation slug
        # to one that's redirecting via SlugRedirect.
        okind = models.OrganisationKind.objects.create(
            name="Example Organisations",
            slug="example-organisations",
        )
        organisation_redirected_to = models.Organisation.objects.create(
            name='The Ministry of Silly Walks',
            slug='ms-walks',
            kind=okind,
        )
        existing_redirect = SlugRedirect.objects.create(
            new_object=organisation_redirected_to,
            old_object_slug='msw',
        )
        other_organisation = models.Organisation(
            name='Ministry of Sensible Walks',
            slug='msw',
            kind=okind,
        )
        with self.assertRaises(ValidationError):
            other_organisation.clean_fields()


class PersonPlaceTest(TestCase):

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
            start_date = '2000-01-01',
            end_date = 'future',
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
            start_date = '2000-01-01',
            end_date = 'future',
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

        # A non-current position associated with place_a
        self.position_f = models.Position.objects.create(
            person = self.person,
            organisation = self.organisation,
            place = self.place_a,
            title = self.position_title_b,
            start_date = '2000-01-01',
            end_date = '2001-12-31',
            category = 'political',
        )

    def test_constituencies_are_distinct(self):
        self.assertEqual(len(self.person.constituencies()), 3)
        self.assertTrue(self.place_a in self.person.constituencies())
        self.assertTrue(self.place_b in self.person.constituencies())
        self.assertTrue(self.place_c in self.person.constituencies())

    def test_constituencies_comes_from_political_positions(self):
        self.assertTrue(self.place_d not in self.person.constituencies())

    def test_place_related_people_no_filter(self):
        related_people = self.place_a.related_people(
            positions_filter=lambda qs: qs)
        self.assertEqual(1, len(related_people))
        self.assertEqual(related_people[0][0],
                         self.person)
        self.assertEqual(set(related_people[0][1]),
                         set([self.position_a, self.position_c]))

    def test_place_related_people_with_filter(self):
        related_people = self.place_a.related_people(
            positions_filter=lambda qs: qs.filter(title__slug='job-title'))
        self.assertEqual(1, len(related_people))
        self.assertEqual(related_people[0][0],
                         self.person)
        self.assertEqual(set(related_people[0][1]),
                         set([self.position_a]))


class SummaryTest(TestCase):

    def setUp(self):
        self.person, _ = models.Person.objects.get_or_create(
            legal_name = "Test Person",
            slug       = 'test-person'
        )
        self.person.save()

    def test_empty_summary_is_false(self):
        # An empty markitup field should be false and have no length so that in
        # the templates its truthiness is correct.
        self.assertFalse( self.person.summary )
        self.assertEqual( len(self.person.summary), 0 )


class RelatedOrganisationTest(TestCase):
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


class NormalizeWhitespaceTest(TestCase):
    def test_normalizing_person_legal_name_whitespace(self):
        person = models.Person.objects.create(
            legal_name='   Alice    Smith   ', slug='alice-smith')
        self.assertEqual('Alice Smith', person.legal_name)


class OverlappingPositionsTests(TestCase):

    def test_overlaps(self):
        organisation_kind = models.OrganisationKind.objects.create(
            name="Example OrganisationKind",
            slug="example-org-kind",
        )
        organisation = models.Organisation.objects.create(
            name="Example Organisation",
            slug="example-org",
            kind=organisation_kind,
        )

        # Some made-up session dates, that we'll test whether various
        # positions overlap with:
        session_start_date = date(2015, 6, 15)
        session_end_date = date(2016, 2, 10)

        blank = ''
        past = ApproximateDate(past=True)
        future = ApproximateDate(future=True)
        full_before_session_start = ApproximateDate(year=2015, month=6, day=10)
        full_after_session_start = ApproximateDate(year=2015, month=7, day=8)
        full_after_session_end = ApproximateDate(year=2016, month=3, day=5)
        month_exactly_session_start = ApproximateDate(year=2015, month=6)
        month_exactly_session_end = ApproximateDate(year=2016, month=2)
        year_exactly_session_start = ApproximateDate(year=2015)
        year_exactly_session_end = ApproximateDate(year=2016)

        # The commented out cases are ones where, because we know the
        # start date must be <= end date, we could say that they don't
        # overlap even though one of the range ends is imprecise, but
        # that turns out to make the implementation much more
        # complicated to deal with that case.

        i = 0
        for overlaps, position_start_date, position_end_date in [
                (True, blank, blank),
                (False, blank, past),
                (True, blank, future),
                (False, blank, full_before_session_start),
                (True, blank, full_after_session_start),
                (True, blank, full_after_session_end),
                (True, blank, month_exactly_session_start),
                (True, blank, month_exactly_session_end),
                (True, blank, year_exactly_session_start),
                (True, blank, year_exactly_session_end),
                (True, past, blank),
                (False, past, past),
                (True, past, future),
                (False, past, full_before_session_start),
                (True, past, full_after_session_start),
                (True, past, full_after_session_end),
                (True, past, month_exactly_session_start),
                (True, past, month_exactly_session_end),
                (True, past, year_exactly_session_start),
                (True, past, year_exactly_session_end),
                (False, future, future),
                (True, full_before_session_start, future),
                (False, full_before_session_start, full_before_session_start),
                (True, full_before_session_start, full_after_session_start),
                (True, full_before_session_start, full_after_session_end),
                (True, full_before_session_start, month_exactly_session_start),
                (True, full_before_session_start, month_exactly_session_end),
                (True, full_before_session_start, year_exactly_session_start),
                (True, full_before_session_start, year_exactly_session_end),
                (True, full_after_session_start, future),
                (True, full_after_session_start, full_after_session_start),
                (True, full_after_session_start, full_after_session_end),
                (True, full_after_session_start, month_exactly_session_start),
                (True, full_after_session_start, month_exactly_session_end),
                (True, full_after_session_start, year_exactly_session_start),
                (True, full_after_session_start, year_exactly_session_end),
                (False, full_after_session_end, future),
                (False, full_after_session_end, full_after_session_end),
                # (False, full_after_session_end, month_exactly_session_end),
                # (False, full_after_session_end, year_exactly_session_end),
                (True, month_exactly_session_start, future),
                # (False, month_exactly_session_start, full_before_session_start),
                (True, month_exactly_session_start, full_after_session_start),
                (True, month_exactly_session_start, full_after_session_end),
                (True, month_exactly_session_start, month_exactly_session_start),
                (True, month_exactly_session_start, month_exactly_session_end),
                (True, month_exactly_session_start, year_exactly_session_start),
                (True, month_exactly_session_start, year_exactly_session_end),
                (True, month_exactly_session_end, future),
                (True, month_exactly_session_end, full_after_session_end),
                (True, month_exactly_session_end, month_exactly_session_end),
                (True, month_exactly_session_end, year_exactly_session_end),
                (True, year_exactly_session_start, future),
                # (False, year_exactly_session_start, full_before_session_start),
                (True, year_exactly_session_start, full_after_session_start),
                (True, year_exactly_session_start, full_after_session_end),
                (True, year_exactly_session_start, month_exactly_session_start),
                (True, year_exactly_session_start, month_exactly_session_end),
                (True, year_exactly_session_start, year_exactly_session_start),
                (True, year_exactly_session_start, year_exactly_session_end),
                (True, year_exactly_session_end, future),
                (True, year_exactly_session_end, full_after_session_end),
                (True, year_exactly_session_end, month_exactly_session_end),
                (True, year_exactly_session_end, year_exactly_session_end),
                ]:
            person = models.Person.objects.create(
                legal_name="Bob '{0}' Smith".format(i),
                slug='bob-{0}-smith'.format(i)
            )
            position = models.Position.objects.create(
                start_date=position_start_date,
                end_date=position_end_date,
                person=person,
                organisation=organisation,
            )
            # Find if the position overlaps with the session dates:
            overlapping_positions = person.position_set.overlapping_dates(
                session_start_date, session_end_date
            )
            if overlaps:
                self.assertEqual(
                    overlapping_positions.count(),
                    1,
                    'No position found, but we expected overlap for position {0} => {1}'.format(
                        repr(position_start_date), repr(position_end_date)
                    )
                )
            else:
                self.assertEqual(
                    overlapping_positions.count(),
                    0,
                    'A position was found, but no overlap was expected for position {0} => {1}'.format(
                        repr(position_start_date), repr(position_end_date)
                    )
                )
            # Now clean up the objects we just created
            person.delete()
            position.delete()
            i += 1


class PersonEveryPoliticianUUIDTest(TestCase):
    def setUp(self):
        self.person = models.Person.objects.create(legal_name="Bob Smith", slug="bob-smith")

    def test_returns_none_with_no_identifier(self):
        self.assertEqual(self.person.everypolitician_uuid, None)

    def test_returns_uuid(self):
        self.person.identifiers.create(scheme='everypolitician', identifier='99795f75-d2fe-4353-a177-a4b8c8cfc01d')
        self.assertEqual(self.person.everypolitician_uuid, '99795f75-d2fe-4353-a177-a4b8c8cfc01d')
