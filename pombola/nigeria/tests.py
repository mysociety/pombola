import unittest
import doctest
from . import views

from django.test import TestCase

from nose.plugins.attrib import attr

from pombola.info.models import InfoPage

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

@attr(country='nigeria')
class InfoBlogListTest(TestCase):

    def setUp(self):
        self.info_page = InfoPage.objects.create(
            slug='escaping-test',
            kind='blog',
            title='Escaping Test', markdown_content="\nTesting\n\n**Escaped**\n\nContent"
        )

    def tearDown(self):
        self.info_page.delete()

    def test_html_not_escaped(self):
        response = self.client.get('/blog/')
        self.assertNotIn('&lt;p&gt;', response.content)
