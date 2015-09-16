from datetime import date
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django_webtest import WebTest
from django.test.utils import override_settings
from django.test import TestCase, RequestFactory

from mock import patch

from pombola.core.models import Person
from pombola.hansard.models import Entry, Sitting, Source, Venue


def fake_geocoder(country, q, decimal_places=3):
    if q == 'anywhere':
        return []
    elif q == 'Garissa':
        return [
            {'latitude': -0.453,
             'longitude': 39.646,
             'address': u'Garissa, Kenya'}
        ]
    elif q == 'Rift Valley':
        return [
            {'latitude': 0.524,
             'longitude': 35.273,
             'address': u'Rift Valley Railways Eldoret, Eldoret, Kenya'},
            {'latitude': -0.944,
             'longitude': 36.596,
             'address': u'Rift Valley Academy - AIM, Kijabe, Kenya'},
            {'latitude': 0.0,
             'longitude': 36.0,
             'address': u'Eastern Rift Valley, Kenya'}
        ]
    else:
        raise Exception, u"Unexpected input to fake_geocoder: {}".format(q)

# If there's no COUNTRY_APP set then the GeocodeView will fail, so use
# kenya for testing location search:

@override_settings(COUNTRY_APP='kenya')
class SearchViewTest(WebTest):

    def setUp(self):
        self.search_location_url = reverse('core_geocoder_search')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_unknown_place(self, mocked_geocoder):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, 'anywhere'))
        results_div = response.html.find('div', class_='geocoded_results')
        self.assertIsNone(results_div)
        mocked_geocoder.assert_called_once_with(q='anywhere', country='ke')

    def get_search_result_list_items(self, query_string):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, query_string))
        results_div = response.html.find('div', class_='geocoded_results')
        return results_div.find('ul').findAll('li')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_single_result_place(self, mocked_geocoder):
        lis = self.get_search_result_list_items('Garissa')
        self.assertEqual(len(lis), 1)
        self.assertEqual(lis[0].a['href'], '/place/latlon/-0.453,39.646/')
        mocked_geocoder.assert_called_once_with(q='Garissa', country='ke')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_multiple_result_place(self, mocked_geocoder):
        lis = self.get_search_result_list_items('Rift Valley')
        self.assertEqual(len(lis), 3)
        self.assertEqual(lis[0].a['href'], '/place/latlon/0.524,35.273/')
        self.assertEqual(lis[1].a['href'], '/place/latlon/-0.944,36.596/')
        self.assertEqual(lis[2].a['href'], '/place/latlon/0.0,36.0/')
        mocked_geocoder.assert_called_once_with(q='Rift Valley', country='ke')


@unittest.skipUnless(
    settings.ENABLED_FEATURES['hansard'],
    'Requires hansard app to be enabled',
    )
class SearchPaginationTest(TestCase):
    def setUp(self):
        from pombola.search.views import HansardSearchView
        self.hsv = HansardSearchView

        self.factory = RequestFactory()

        # We need four hansard entries, three containing a term, and one not.
        # Then we can set the pagination limit to 2.

        venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            )

        source = Source.objects.create(
            name='Test Source',
            date=date(2015, 2, 1),
            url='http://example.com/example',
            )

        sitting1 = Sitting.objects.create(
            venue=venue,
            source=source,
            start_date=date(2015, 1, 1),
            )

        sitting2 = Sitting.objects.create(
            venue=venue,
            source=source,
            start_date=date(2015, 1, 2),
            )

        person = Person.objects.create(
            legal_name='Test Person',
            slug='test-person',
            )

        blancmange1 = Entry.objects.create(
            type='speech',
            sitting=sitting1,
            page_number=1,
            text_counter=1,
            speaker=person,
            content='Lovely blancmange!',
            )

        blancmange2 = Entry.objects.create(
            type='speech',
            sitting=sitting1,
            page_number=1,
            text_counter=2,
            speaker=person,
            content='More blancmange!',
            )

        blancmange3 = Entry.objects.create(
            type='speech',
            sitting=sitting2,
            page_number=1,
            text_counter=1,
            speaker=person,
            content='More lovely blancmange!',
            )

        nothing_much = Entry.objects.create(
            type='speech',
            sitting=sitting1,
            page_number=1,
            text_counter=3,
            speaker=person,
            content='Nothing to see here',
            )

        self.old_results_per_page = self.hsv.results_per_page
        self.hsv.results_per_page = 2

    def tearDown(self):
        self.hsv.results_per_page = self.old_results_per_page

    def test_pagination(self):
        request = self.factory.get(
            '/customer/details',
            data={'q': 'blancmange', 'order': 'adate'}
            )

        response = self.hsv.as_view()(request)
        paginator = response.context_data['paginator']
        page = response.context_data['page_obj']

        self.assertEqual(paginator._count, 3)
        self.assertEqual(paginator._num_pages, 2)
        self.assertEqual(page.number, 1)
