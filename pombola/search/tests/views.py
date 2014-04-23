from django.core.urlresolvers import reverse
from django_webtest import WebTest
from django.test.utils import override_settings

from mock import patch

def fake_geocoder(country, q, decimal_places=3):
    if q == 'anywhere':
        return []
    elif q == 'Cape Town':
        return [
            {'latitude': -33.925,
             'longitude': 18.424,
             'address': u'Cape Town, South Africa'}
        ]
    elif q == 'Trafford Road':
        return [
            {'latitude': -29.814,
             'longitude': 30.839,
             'address': u'Trafford Road, Pinetown 3610, South Africa'},
            {'latitude': -33.969,
             'longitude': 18.703,
             'address': u'Trafford Road, Cape Town 7580, South Africa'},
            {'latitude': -32.982,
             'longitude': 27.868,
             'address': u'Trafford Road, East London 5247, South Africa'}
        ]
    else:
        raise Exception, u"Unexpected input to fake_geocoder: {}".format(q)

# If there's no COUNTRY_APP set then the GeocodeView will fail, so use
# south_africa for testing location search:

@override_settings(COUNTRY_APP='south_africa')
class SearchViewTest(WebTest):

    def setUp(self):
        self.search_location_url = reverse('core_geocoder_search')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_unknown_place(self, mocked_geocoder):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, 'anywhere'))
        results_div = response.html.find('div', class_='geocoded_results')
        lis = results_div.find('ul').findAll('li')
        self.assertEqual(len(lis), 0)
        mocked_geocoder.assert_called_once_with(q='anywhere', country='za')

    def get_search_result_list_items(self, query_string):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, query_string))
        results_div = response.html.find('div', class_='geocoded_results')
        return results_div.find('ul').findAll('li')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_single_result_place(self, mocked_geocoder):
        lis = self.get_search_result_list_items('Cape Town')
        self.assertEqual(len(lis), 1)
        self.assertEqual(lis[0].a['href'], '/place/latlon/-33.925,18.424/')
        mocked_geocoder.assert_called_once_with(q='Cape Town', country='za')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_multiple_result_place(self, mocked_geocoder):
        lis = self.get_search_result_list_items('Trafford Road')
        self.assertEqual(len(lis), 3)
        self.assertEqual(lis[0].a['href'], '/place/latlon/-29.814,30.839/')
        self.assertEqual(lis[1].a['href'], '/place/latlon/-33.969,18.703/')
        self.assertEqual(lis[2].a['href'], '/place/latlon/-32.982,27.868/')
        mocked_geocoder.assert_called_once_with(q='Trafford Road', country='za')
