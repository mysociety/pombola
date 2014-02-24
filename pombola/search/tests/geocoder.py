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
            {'latitude': -33.642, 'longitude': 19.449, 'address': u'High Street, Worcester 6850, South Africa'},
        ]
        for expected in expected_results:
            self.assertIn(expected, results)

        # These are how many we expect
        self.assertEqual(len(results), 30)

    def test_dedupe_matches(self):
        results = geocoder(country=self.country, q="Cape Town")

        # These are well known results that should be in those returned
        expected_results = [
            {'address': u'Cape Town, South Africa', 'latitude': -33.925, 'longitude': 18.424},
        ]

        # These are how many we expect
        self.assertEqual(results, expected_results)

