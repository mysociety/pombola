from django.conf import settings
from django.utils import unittest

from ..geocoder import geocoder


class GeocoderTests(unittest.TestCase):

    def setUp(self):
        self.country = 'za'

    def test_no_match(self):
        results = geocoder(country=self.country, q="Place that does not exist")
        self.assertEqual(results, [])

    def test_one_match(self):
        results = geocoder(country=self.country, q="East London")
        self.assertEqual(
            results,
            [{
                'address': 'East London, South Africa',
                'latitude': -32.983,
                'longitude': 27.867
            }]
        )

    def test_many_matches(self):
        results = geocoder(country=self.country, q="High Street")

        # These are well known results that should be in those returned
        expected_results = [
            {'latitude': -26.195, 'longitude': 28.0,   'address': u'High Street, Johannesburg 2092, South Africa'},
            {'latitude': -25.786, 'longitude': 28.261, 'address': u'High Street, Pretoria, South Africa'},
        ]
        for expected in expected_results:
            self.assertTrue(expected in results)

        # These are how many we expect
        self.assertEqual(len(results), 10)

