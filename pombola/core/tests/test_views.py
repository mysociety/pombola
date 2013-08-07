import random
import datetime

from django.core import exceptions
from django_webtest import WebTest
from django_date_extensions.fields import ApproximateDate

from pombola.core import models

class PositionTest(WebTest):
    def setUp(self):
        person = models.Person.objects.create(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )
        
        organisation_kind = models.OrganisationKind.objects.create(
            name = 'Foo',
            slug = 'foo',
        )
        organisation_kind.save()

        organisation = models.Organisation.objects.create(
            name = 'Test Org',
            slug = 'test-org',
            kind = organisation_kind,
        )
        
        title = models.PositionTitle.objects.create(
            name = 'Test title',
            slug = 'test-title',
        )
        title2 = models.PositionTitle.objects.create(
            name = 'Test position with place',
            slug = 'test-position-with-place',
        )

        models.Position.objects.create(
            person = person,
            title  = title,
            organisation = organisation,
        )

        place_kind_constituency = models.PlaceKind.objects.create(
            name='Constituency',
            slug='constituency',
        )

        bobs_place = models.Place.objects.create(
            name="Bob's Place",
            slug='bobs_place',
            kind=place_kind_constituency,
        )

        models.Position.objects.create(
            person = person,
            title  = title2,
            organisation = organisation,
            place = bobs_place,
        )

    def test_position_page(self):
        # List of people with position title
        self.app.get('/position/nonexistent-position-title/', status=404)
        resp = self.app.get('/position/test-title/')
        resp.mustcontain('Test Person')
        resp = self.app.get('/position/test-title/?view=grid')
        # List of people with position title at orgs of a certain kind
        self.app.get('/position/test-title/nonexistent-org-kind/', status=404)
        resp = self.app.get('/position/test-title/foo/')
        resp.mustcontain('Test Person')
        # List of people with position title at particular org
        self.app.get('/position/test-title/foo/nonexistent-org/', status=404)
        resp = self.app.get('/position/test-title/foo/test-org/')
        resp.mustcontain('Test Person')

    def test_position_on_person_page(self):
        resp = self.app.get('/person/test-person/experience/')
        resp.mustcontain('Test title', 'of <a href="/organisation/test-org/">Test Org</a>')

    def test_organisation_page(self):
        self.app.get('/organisation/missing-org/', status=404)
        resp = self.app.get('/organisation/test-org/')
        resp.mustcontain('Test Org')
        resp = self.app.get('/organisation/test-org/people/')
        resp.mustcontain('Test Person')
        resp = self.app.get('/organisation/is/foo/')
        resp.mustcontain('Test Org')
        resp = self.app.get('/organisation/is/foo/?order=place')
        resp.mustcontain('Test Org')

    def test_place_page(self):
        self.app.get('/place/is/constituency/')
        self.app.get('/place/bobs_place/')
