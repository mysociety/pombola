import os
import datetime
# import time
# import json
# import tempfile
# import subprocess

from django.test import TestCase
from django.utils import unittest

from django_date_extensions.fields import ApproximateDate

# from hansard.kenya_parser import KenyaParser, KenyaParserCouldNotParseTimeString

from core.models import Person, PositionTitle, Position
from hansard.models import Source, Sitting, Entry, Venue, Alias

from hansard.ghana_parser import parse


class GhanaParserTest(TestCase):
    basedir = os.path.abspath(os.path.dirname( __file__ ))
    sample = os.path.join(basedir, 'hansard-sample-001.txt')
    
    entries = None
    head = None


    @classmethod
    def setUpClass(cls):
        cls.head, cls.entries = parse(open(cls.sample, 'r').readlines())

    @classmethod
    def tearDownClass(cls):
        pass

    def test_parse_time_string(self):
        
        data = {
            '1.00 p.m.':  datetime.time(13),
            '1.00 a.m.':  datetime.time(1),
            '12.00 p.m.': datetime.time(12), # am and pm make no sense at noon or midnight - but define what we want to happen
            '12.30 p.m.': datetime.time(12, 30)
        }
        
        for s, t in data.items():
            self.assertEqual(parse_time(s), t)

        self.assertNone(parse_time('foo.bar'))
        

    def t1est_header_001(self):
        self.assertEqual(4, self.head['series'])
        self.assertEqual(76, self.head['volume'])
        self.assertEqual(13, self.head['number'])
        self.assertEqual(datetime.date(2012, 2, 14), self.head['date'])
        self.assertEqual(datetime.time(10, 40), self.head['time'])

    def t1est_entries_001(self):
        t = datetime.time(10, 40)

        x = self.entries[0]
        self.assertTrue(x['text'].lower().endswith('speaker in the chair'))
        self.assertEqual(t, x['time'])

        x = self.entries[1]
        self.assertEqual('PRAYERS', x['text'])
        self.assertEqual(t, x['time'])

        topic = 'Votes and Proceedings and the Official Report'
        

        speeches = [x for x in self.entries if x['kind'] is 'speech']

        self.assertEqual(169, len(speeches))
        
        x = self.entries[0]

        self.assertEqual(topic, x['topic'])
        self.assertEqual('Madam Speaker', x['name'])


        x = self.entries[-1]
        self.assertEqual('ADJOURNMENT', x['text'])
        self.assertEqual(datetime.time(13, 20), x['time'])
        self.assertEqual(datetime.datetime(2012, 2, 15, 10), x['next'])

    def test_page_order_001(self):
        pass
