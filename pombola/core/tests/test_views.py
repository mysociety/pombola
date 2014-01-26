from django_webtest import WebTest

from pombola.core import models

class PositionTest(WebTest):
    def tearDown(self):
        self.position.delete()
        self.position2.delete()
        self.person.delete()
        self.organisation.delete()
        self.organisation_kind.delete()
        self.title.delete()
        self.title2.delete()
        self.bobs_place.delete()
        self.place_kind_constituency.delete()

    def setUp(self):
        self.person = models.Person.objects.create(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )
        
        self.organisation_kind = models.OrganisationKind.objects.create(
            name = 'Foo',
            slug = 'foo',
        )
        self.organisation_kind.save()

        self.organisation = models.Organisation.objects.create(
            name = 'Test Org',
            slug = 'test-org',
            kind = self.organisation_kind,
        )
        
        self.title = models.PositionTitle.objects.create(
            name = 'Test title',
            slug = 'test-title',
        )
        self.title2 = models.PositionTitle.objects.create(
            name = 'Test position with place',
            slug = 'test-position-with-place',
        )

        self.position = models.Position.objects.create(
            person = self.person,
            title  = self.title,
            organisation = self.organisation,
        )

        self.place_kind_constituency = models.PlaceKind.objects.create(
            name='Constituency',
            slug='constituency',
        )

        self.bobs_place = models.Place.objects.create(
            name="Bob's Place",
            slug='bobs_place',
            kind=self.place_kind_constituency,
        )

        self.position2 = models.Position.objects.create(
            person = self.person,
            title  = self.title2,
            organisation = self.organisation,
            place = self.bobs_place,
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
