import unittest
import geocode
import pprint
import os

class Geocode(unittest.TestCase):
    def setUp(self):
        pass

    def test_find_address(self):
        
        tests = [
            {
                # no results for this
                'input': 'Foo Bar Bad Place',
                'output': [],
            },
            {
                # one result
                'input': 'Nairobi',
                'output': [
                    {
                        'name': u'Nairobi',
                        'lat': '-1.29207',
                        'lng': '36.82195',
                    },
                ],
            },
            {
                # many results - some outside Kenya (should be filtered)
                'all_tests_only': True, # fickle test as it changes
                'input': 'Kenyatta',
                'output':  [
                    { 'name': u'Mombasa-Malindi Rd, Malindi', 'lat': '-3.21585', 'lng': '40.11737', },
                    { 'name': u'Kenyatta Ave, Nanyuki',       'lat': '0.01319',  'lng': '37.07745', },
                    { 'name': u'C77, Nyahururu',              'lat': '0.03608',  'lng': '36.36455', },
                    { 'name': u'Kenyatta Ave, Naivasha',      'lat': '-0.72551', 'lng': '36.44472', },
                    { 'name': u'Kenyatta Ave, Nairobi',       'lat': '-1.28487', 'lng': '36.82057', },
                    { 'name': u'Kenyatta Rd, Nyeri',          'lat': '-0.42570', 'lng': '36.95296', },
                    ],
            }
        ]

        for test in tests:
            if test.get('all_tests_only') and not os.environ.get('ALL_TESTS'): continue
            output = geocode.find( test['input'])
            self.assertEqual( output, test['output'] )


    def test_coord_to_areas(self):
        
        tests = [
        {
            # Valid location
            'lat': '0.03608',
            'lng': '36.36455',
            'output': {
                u'PRO': {'mapit_id': 4820, 'name': u'Rift Valley'},
                u'DIV': {'mapit_id': 5049, 'name': u'Rumuruti'},
                u'DIS': {'mapit_id': 4855, 'name': u'Laikipia'},
            },
        },
        {
            # location outside Kenya
            'lat': '0',
            'lng': '0',
            'output': {
            },
        },
            
        ]

        for test in tests:
            output = geocode.coord_to_areas( lat=test['lat'], lng=test['lng'] )
            self.assertEqual( output, test['output'] )

