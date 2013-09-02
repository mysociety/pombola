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
        self.assertEqual(
            results,
            [
                {'latitude': -26.195, 'longitude': 28.0,   'address': u'High Street, Johannesburg 2092, South Africa'},
                {'latitude': -33.31,  'longitude': 26.527, 'address': u'High Street, Grahamstown 6139, South Africa'},
                {'latitude': -26.238, 'longitude': 28.363, 'address': u'High Street, Brakpan 1540, South Africa'},
                {'latitude': -31.295, 'longitude': 25.829, 'address': u'High Street, Steynsburg 5920, South Africa'},
                {'latitude': -26.254, 'longitude': 28.058, 'address': u'High Street, Johannesburg South, South Africa'},
                {'latitude': -28.235, 'longitude': 28.308, 'address': u'High Street, Bethlehem 9701, South Africa'},
                {'latitude': -25.786, 'longitude': 28.261, 'address': u'High Street, Pretoria, South Africa'},
                {'latitude': -33.735, 'longitude': 23.347, 'address': u'High Street, Haarlem 6467, South Africa'},
                {'latitude': -33.589, 'longitude': 26.905, 'address': u'High Street, Port Alfred 6170, South Africa'},
                {'latitude': -29.722, 'longitude': 31.07,  'address': u'High Street, Umhlanga, South Africa'}
            ]
        )
