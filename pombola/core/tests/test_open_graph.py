from django.test import TestCase
from django.core.urlresolvers import reverse

from info.models import InfoPage

from pombola.core import models


class OpenGraphTest(TestCase):
    def test_open_graph_tags_on_homepage(self):
        response = self.client.get('/')
        self.assertContains(response, '<meta property="og:title" content="example.com" />')
        self.assertContains(response, '<meta property="og:type" content="website" />')
        self.assertContains(response, '<meta property="og:url" content="http://testserver/" />')

    def test_open_graph_tags_for_person(self):
        person = models.Person.objects.create(
            slug='bob',
            legal_name='Bob Test',
            summary='Test summary',
            given_name='Bob',
            family_name='Test',
            gender='male')

        response = self.client.get(reverse('person', kwargs={'slug': person.slug}))

        self.assertContains(response, '<meta property="og:title" content="Bob Test" />')
        self.assertContains(response, '<meta property="og:site_name" content="example.com" />')
        self.assertContains(response, '<meta property="og:type" content="profile" />')
        self.assertContains(response, '<meta property="og:url" content="http://testserver/person/bob/" />')
        self.assertContains(response, '<meta property="og:description" content="Test summary" />')
        self.assertContains(response, '<meta property="profile:first_name" content="Bob" />')
        self.assertContains(response, '<meta property="profile:last_name" content="Test" />')
        self.assertContains(response, '<meta property="profile:gender" content="male" />')

    def test_open_graph_tags_for_orgs(self):
        organisation_kind = models.OrganisationKind.objects.create(
            name='Political',
            slug='political')

        org = models.Organisation.objects.create(
            slug='test-org',
            name='Test Org',
            summary='A Test Org.',
            kind=organisation_kind)

        response = self.client.get(reverse('organisation', kwargs={'slug': org.slug}))

        self.assertContains(response, '<meta property="og:title" content="Test Org" />')
        self.assertContains(response, '<meta property="og:site_name" content="example.com" />')
        self.assertContains(response, '<meta property="og:type" content="website" />')
        self.assertContains(response, '<meta property="og:url" content="http://testserver/organisation/test-org/" />')
        self.assertContains(response, '<meta property="og:description" content="A Test Org." />')

    def test_open_graph_tags_for_places(self):
        place_kind = models.PlaceKind.objects.create(
            name='Test Place',
            slug='test-place')

        place = models.Place.objects.create(
            name='The Place',
            slug='place',
            kind=place_kind)

        response = self.client.get(reverse('place', kwargs={'slug': place.slug}))

        self.assertContains(response, '<meta property="og:title" content="The Place" />')
        self.assertContains(response, '<meta property="og:site_name" content="example.com" />')
        self.assertContains(response, '<meta property="og:type" content="place" />')
        self.assertContains(response, '<meta property="og:url" content="http://testserver/place/place/" />')

    def test_open_graph_tags_for_blog_posts(self):
        post = InfoPage.objects.create(
            slug='post',
            title='Example title',
            raw_content='Example content',
            use_raw=True,
            kind=InfoPage.KIND_BLOG,
        )

        response = self.client.get(reverse('info_blog', kwargs={'slug': post.slug}))

        self.assertContains(response, '<meta property="og:title" content="Example title" />')
        self.assertContains(response, '<meta property="og:site_name" content="example.com" />')
        self.assertContains(response, '<meta property="og:type" content="article" />')
        self.assertContains(response, '<meta property="og:url" content="http://testserver/blog/post" />')
        self.assertContains(response, '<meta property="article:published_time" content="{}" />'.format(post.publication_date.isoformat()))
