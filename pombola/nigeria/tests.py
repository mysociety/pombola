import unittest
import doctest
from . import views

from django.test import TestCase

from nose.plugins.attrib import attr

# Needed to run the doc tests in views.py

def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(views))
    return suite

@attr(country='nigeria')
class HomeViewTest(TestCase):

    def test_homepage_context(self):
        response = self.client.get('/')
        self.assertIn('featured_person', response.context)
        self.assertIn('featured_persons', response.context)
        self.assertIn('editable_content', response.context)
