import json
import os

from django.utils import unittest

from ..geocoder import geocoder

import pygeocoder

from mock import patch, Mock


test_data_directory = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        'geocoder-test-data'))

mocked_place_results = {
    'East London': 'google_east_london.json',
    'Cape Town': 'google_cape_town.json',
    'High Street': 'google_high_street.json'}

def fake_geocode(q, **kwargs):
    if q == "Place that does not exist":
        raw_result = []
    elif q in mocked_place_results:
        with open(os.path.join(test_data_directory,
                               mocked_place_results[q])) as f:
            raw_result = json.load(f)
    else:
        raise Exception, "Not yet faked..."
    return Mock(raw=raw_result)

class GeocoderTests(unittest.TestCase):

    def setUp(self):
        self.country = 'za'

    @patch.object(pygeocoder.Geocoder, 'geocode', side_effect=fake_geocode)
    def test_no_match(self, mocked_class_method):
        results = geocoder(country=self.country, q="Place that does not exist")
        self.assertEqual(results, [])
        mocked_class_method.assert_called_once_with(
            'Place that does not exist', components='country:za')

    @patch.object(pygeocoder.Geocoder, 'geocode', side_effect=fake_geocode)
    def test_one_match(self, mocked_class_method):
        results = geocoder(country=self.country, q="East London")
        self.assertEqual(
            results,
            [{
                'address': 'East London, South Africa',
                'latitude': -32.983,
                'longitude': 27.867
            }]
        )
        mocked_class_method.assert_called_once_with(
            'East London', components='country:za')

    @patch.object(pygeocoder.Geocoder, 'geocode', side_effect=fake_geocode)
    def test_many_matches(self, mocked_class_method):
        results = geocoder(country=self.country, q="High Street")

        # These are well known results that should be in those returned
        expected_results = [
            {'latitude': -26.195,
             'longitude': 28.0,
             'address': u'High Street, Johannesburg 2092, South Africa'},
            {'latitude': -33.642,
             'longitude': 19.449,
             'address': u'High Street, Worcester 6850, South Africa'},
        ]
        for expected in expected_results:
            self.assertIn(expected, results)

        # These are how many we expect
        self.assertEqual(len(results), 30)

        mocked_class_method.assert_called_once_with(
            'High Street', components='country:za')

    @patch.object(pygeocoder.Geocoder, 'geocode', side_effect=fake_geocode)
    def test_dedupe_matches(self, mocked_class_method):
        results = geocoder(country=self.country, q="Cape Town")

        # These are well known results that should be in those returned
        expected_results = [
            {'address': u'Cape Town, South Africa',
             'latitude': -33.925,
             'longitude': 18.424},
        ]

        # These are how many we expect
        self.assertEqual(results, expected_results)

        mocked_class_method.assert_called_once_with(
            'Cape Town', components='country:za')
