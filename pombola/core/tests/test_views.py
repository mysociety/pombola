from BeautifulSoup import NavigableString
from contextlib import contextmanager
from django_webtest import WebTest
from django.contrib.auth.models import User
from django.test import TestCase

from pombola.core import models
from pombola.slug_helpers.models import SlugRedirect


class HomeViewTest(TestCase):

    def test_homepage_context(self):
        response = self.client.get('/')
        self.assertIn('featured_person', response.context)
        self.assertIn('featured_persons', response.context)


class PositionViewTest(WebTest):

    def setUp(self):
        self.person = models.Person.objects.create(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )

        self.person_hidden = models.Person.objects.create(
            legal_name = 'Test Hidden Person',
            slug       = 'test-hidden-person',
            hidden     = True
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

        self.org_slug_redirect = SlugRedirect.objects.create(
            old_object_slug='test-Blah-org',
            new_object=self.organisation,
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

        self.place_slug_redirect = SlugRedirect.objects.create(
            old_object_slug='old_bobs_place',
            new_object=self.bobs_place,
        )

        self.position2 = models.Position.objects.create(
            person = self.person,
            title  = self.title2,
            organisation = self.organisation,
            place = self.bobs_place,
        )

        self.position_hidden_person = models.Position.objects.create(
            person = self.person_hidden,
            title  = self.title,
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

    def get_links_to_people(self, soup):
        def wanted_link(a):
            if not a.has_attr('href'):
                return False
            url = a['href']
            person_url = url.startswith('/person/')
            disqush_fragment = url.endswith('#disqus_thread')
            return person_url and not disqush_fragment
        return set(a['href'] for a in soup.findAll('a') if wanted_link(a))

    def test_position_page_hidden_person_not_linked(self):
        resp = self.app.get('/position/test-title/')
        resp.mustcontain('Test Person')
        resp.mustcontain('Test Hidden Person')
        self.assertEqual(
            set([u'/person/test-person/']),
            self.get_links_to_people(resp.html)
        )

    def test_position_on_person_page(self):
        resp = self.app.get('/person/test-person/experience/')
        resp.mustcontain('Test title', 'of <a href="/organisation/test-org/">Test Org</a>')

    def test_organisation_page(self):
        self.app.get('/organisation/missing-org/', status=404)
        with self.assertNumQueries(8):
            resp = self.app.get('/organisation/test-org/')
        resp.mustcontain('Test Org')
        resp = self.app.get('/organisation/test-org/people/')
        resp.mustcontain('Test Person')
        resp = self.app.get('/organisation/is/foo/')
        resp.mustcontain('Test Org')
        resp = self.app.get('/organisation/is/foo/?order=place')
        resp.mustcontain('Test Org')

    def test_organisation_slug_redirects(self):
        resp = self.app.get('/organisation/test-Blah-org/')
        self.assertRedirects(resp, '/organisation/test-org/', status_code=302)

    def test_organisation_contact_details_slug_redirects(self):
        resp = self.app.get('/organisation/test-Blah-org/contact_details/')
        self.assertRedirects(resp, '/organisation/test-org/contact_details/', status_code=302)

    def test_organisation_apperances_slug_redirects(self):
        resp = self.app.get('/organisation/test-Blah-org/people/')
        self.assertRedirects(resp, '/organisation/test-org/people/', status_code=302)

    def test_place_page(self):
        self.app.get('/place/is/constituency/')
        self.app.get('/place/bobs_place/')

    def test_place_page_slug_redirects(self):
        resp = self.app.get('/place/old_bobs_place/')
        self.assertRedirects(resp, '/place/bobs_place/', status_code=302)

    def test_place_page_people_slug_redirects(self):
        resp = self.app.get('/place/old_bobs_place/people/')
        self.assertRedirects(resp, '/place/bobs_place/people/', status_code=302)

    def test_place_page_places_slug_redirects(self):
        resp = self.app.get('/place/old_bobs_place/places/')
        self.assertRedirects(resp, '/place/bobs_place/places/', status_code=302)

    def test_place_page_hidden_person_not_linked(self):
        resp = self.app.get('/place/bobs_place/')
        self.assertEqual(
            set([u'/person/test-person/']),
            self.get_links_to_people(resp.html)
        )


class TestPersonView(WebTest):

    def setUp(self):
        self.alf = models.Person.objects.create(
            legal_name="Alfred Smith",
            slug='alfred-smith',
            date_of_birth='1960-04-01',
        )
        self.deceased = models.Person.objects.create(
            legal_name="Deceased Person",
            slug='deceased-person',
            date_of_birth='1965-12-31',
            date_of_death='2010-01-01',
        )
        self.superuser = User.objects.create(
            username='admin',
            is_superuser=True
        )
        self.slug_redirect = SlugRedirect.objects.create(
            old_object_slug='Alfred--Smith',
            new_object=self.alf,
        )

    def test_person_view_redirect(self):
        resp = self.app.get('/person/alfred-smith')
        self.assertRedirects(resp, '/person/alfred-smith/', status_code=301)

    def test_person_smoke_test(self):
        resp = self.app.get('/person/alfred-smith/')
        self.assertTrue(resp)

    def test_person_slug_redirects(self):
        resp = self.app.get('/person/Alfred--Smith/')
        self.assertRedirects(resp, '/person/alfred-smith/', status_code=302)

    def test_person_experience_slug_redirects(self):
        resp = self.app.get('/person/Alfred--Smith/experience/')
        self.assertRedirects(resp, '/person/alfred-smith/experience/', status_code=302)

    def test_person_appearances_slug_redirects(self):
        resp = self.app.get('/person/Alfred--Smith/appearances/')
        self.assertRedirects(resp, '/person/alfred-smith/appearances/', status_code=302)

    @contextmanager
    def with_hidden_person(self):
        try:
            self.alf.hidden = True
            self.alf.save()
            yield
        finally:
            self.alf.hidden = False
            self.alf.save()

    def test_person_hidden(self):
        with self.with_hidden_person():
            resp = self.app.get('/person/alfred-smith/', status=404)
            self.assertEqual(resp.status_code, 404)

    def test_person_hidden_superuser(self):
        with self.with_hidden_person():
            resp = self.app.get('/person/alfred-smith/', user=self.superuser)
            self.assertTrue(resp)

    def get_next_sibling(self, original_element, tag_name_to_find):
        current = original_element
        while True:
            current = current.next_sibling
            self.assertIsNotNone(current)
            if type(current) == NavigableString:
                continue
            if current.name == tag_name_to_find:
                return current
        return None

    def get_personal_details(self, soup):
        heading = soup.find('h2', text='Personal Details')
        dl = self.get_next_sibling(heading, 'dl')
        terms = [dt.text.strip() for dt in dl.find_all('dt')]
        definitions = [dd.text.strip() for dd in dl.find_all('dd')]
        return dict(zip(terms, definitions))

    def test_person_birth_date_no_death_date(self):
        resp = self.app.get('/person/alfred-smith/')
        personal_details = self.get_personal_details(resp.html)
        keys = personal_details.keys()
        self.assertIn('Born', keys)
        self.assertNotIn('Died', keys)
        self.assertEqual(
            '1st April 1960',
            personal_details['Born'],
        )

    def test_person_birth_date_and_death_date(self):
        resp = self.app.get('/person/deceased-person/')
        personal_details = self.get_personal_details(resp.html)
        keys = personal_details.keys()
        self.assertIn('Born', keys)
        self.assertIn('Died', keys)
        self.assertEqual(
            '31st December 1965',
            personal_details['Born'],
        )
        self.assertEqual(
            '1st January 2010',
            personal_details['Died'],
        )
