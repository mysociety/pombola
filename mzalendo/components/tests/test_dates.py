import unittest

from components.models import *

class TestDates(unittest.TestCase):

    def test_partial_dates(self):
        null = {u'start': None, u'end': None, u'formatted': u''}
        complete_year = {u'start': u'2008-01-01T00:00:00.000Z', u'end': u'2008-12-31T00:00:00.000Z', u'formatted': u'Jan 1 - Dec 31, 2008'}
        complete_month = {u'start': u'2012-02-01T00:00:00.000Z', u'end': u'2012-02-29T00:00:00.000Z', u'formatted': u'Feburary 2012'}
        two_complete_months = {u'start': u'2007-03-01T00:00:00.000Z', u'end': u'2007-04-30T00:00:00.000Z', u'formatted': u'February and April 2007'}

        null_parsed = PartialDate.create(null)
        self.assertEqual(null_parsed, None)

        complete_year_parsed = PartialDate.create(complete_year)
        self.assertEqual(complete_year_parsed.pretty_print(), "2008")

        complete_month_parsed = PartialDate.create(complete_month)
        self.assertEqual(complete_month_parsed.pretty_print(), "2012-02")

        two_complete_months_parsed = PartialDate.create(two_complete_months)
        self.assertEqual(two_complete_months_parsed.pretty_print(), "2007-03-01 to 2007-04-30")

    def test_errors(self):
        with self.assertRaises(Exception):
            pd = PartialDate.create({})
        with self.assertRaises(Exception):
            pd = PartialDate({})
