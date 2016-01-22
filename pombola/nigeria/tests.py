import unittest
import doctest
import re
from . import views

from django.test import TestCase
from django_webtest import WebTest

from nose.plugins.attrib import attr

from mapit.models import Area, CodeType, NameType, Type
from pombola.core.models import (
    Place, PlaceKind, Person, Position, PositionTitle)
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


@attr(country='nigeria')
class NGSearchViewTest(WebTest):

    def setUp(self):
        self.poll_unit_code_type = CodeType.objects.create(
            code='poll_unit',
            description='Polling Unit Number',
            )

        self.poll_unit_name_type = NameType.objects.create(
            code='poll_unit',
            description='Polling Unit Number names',
            )

        self.state_type = Type.objects.create(
            code='STA',
            description='State',
            )

        self.mapit_test_state = Area.objects.create(
            name="Ondo",
            type=self.state_type,
            )

        self.mapit_test_state.codes.get_or_create(
            type=self.poll_unit_code_type,
            code="ON",
         )

        self.mapit_test_state.names.get_or_create(
            type=self.poll_unit_name_type,
            name="ONDO"
        )

        self.place_kind = PlaceKind.objects.create(
            slug='pk_test', name='PK Test')

        self.place_state = Place.objects.create(
            kind=self.place_kind,
            slug="place_test",
            name="Test State Name",
            mapit_area=self.mapit_test_state
        )

        self.governor = Person.objects.create(
            slug="governor_test",
            legal_name="Test Gov",
        )

        self.gov_title = PositionTitle.objects.create(
            slug="governor"
        )

        self.position = Position.objects.create(
            title=self.gov_title,
            place=self.place_state,
            person=self.governor
        )

        self.lga_type = Type.objects.create(
            code='LGA',
            description='LGA',
            )

        self.mapit_test_lga = Area.objects.create(
            name="Akoko South West",
            type=self.lga_type,
            )

        self.mapit_test_lga.codes.get_or_create(
            type=self.poll_unit_code_type,
            code="ON:4",
         )

        self.mapit_test_lga.names.get_or_create(
            type=self.poll_unit_name_type,
            name="AKOKO SOUTH WEST"
        )

        self.ward_type = Type.objects.create(
            code='WRD',
            description='Ward',
            )

        self.mapit_test_ward = Area.objects.create(
            name="Test Ward",
            type=self.ward_type,
            parent_area = self.mapit_test_lga,
            )

        self.mapit_test_ward.codes.get_or_create(
            type=self.poll_unit_code_type,
            code="ON:4:7",
         )

        self.mapit_test_ward.names.get_or_create(
            type=self.poll_unit_name_type,
            name="Test Ward"
        )

    def test_four_part_pun_is_recognised(self):
        response = self.app.get("/search/?q=01:02:03:04")
        self.assertIn(
            'No results were found for the poll unit number AB:2:3:4',
            response.content
        )

    def test_slash_formatted_pun_is_recognised(self):
        response = self.app.get("/search/?q=01/02/03/04")
        self.assertIn(
            'No results were found for the poll unit number AB:2:3:4',
            response.content
        )

    def test_matching_state(self):
        response = self.app.get("/search/?q=28/04454/09")
        self.assertIn(
            'Best match is the state "ONDO" with poll unit number \'ON\'',
            response.content
        )

    def test_matching_lga(self):
        response = self.app.get("/search/?q=28/04/09")
        self.assertIn(
            'Best match is the local government area "AKOKO SOUTH WEST" with poll unit number \'ON:4\'',
            response.content
        )

    def test_matching_ward(self):
        response = self.app.get("/search/?q=28/04/07")
        self.assertIn(
            'Best match is the ward "Test Ward" with poll unit number \'ON:4:7\'',
            response.content
        )

        self.assertTrue(
            re.search(
                r'<h3>State</h3>\s*<p>\s*<a href="/place/place_test/">Test State Name</a>,\s*current governor <a href="/person/governor_test/">Test Gov</a>',
                response.content
            )
        )
