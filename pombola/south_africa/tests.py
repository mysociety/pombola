from __future__ import division

import re
import os
from datetime import date, time
from StringIO import StringIO
from urlparse import urlparse
from collections import OrderedDict
from datetime import datetime

import requests

from mock import patch, MagicMock

from django.contrib.gis.geos import Polygon, Point
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from django.core.cache import caches

from django.core.urlresolvers import reverse, resolve
from django.core.management import call_command
from django_date_extensions.fields import ApproximateDate
from django_webtest import WebTest

from mapit.models import Type, Area, Geometry, Generation

from django.conf import settings
import json

from speeches.models import Section, Speech
from speeches.tests import create_sections

from info.models import InfoPage

from pombola.core import models
from pombola import south_africa
from pombola.south_africa.views import SAPersonDetail
from pombola.core.views import PersonSpeakerMappingsMixin
from instances.models import Instance
from pombola.interests_register.models import Category, Release, Entry, EntryLineItem

from nose.plugins.attrib import attr
from pygeolib import GeocoderError

def fake_geocoder(country, q, decimal_places=3):
    if q == 'anywhere':
        return []
    elif q == 'Cape Town':
        return [
            {'latitude': -33.925,
             'longitude': 18.424,
             'address': u'Cape Town, South Africa'}
        ]
    elif q == 'Trafford Road':
        return [
            {'latitude': -29.814,
             'longitude': 30.839,
             'address': u'Trafford Road, Pinetown 3610, South Africa'},
            {'latitude': -33.969,
             'longitude': 18.703,
             'address': u'Trafford Road, Cape Town 7580, South Africa'},
            {'latitude': -32.982,
             'longitude': 27.868,
             'address': u'Trafford Road, East London 5247, South Africa'}
        ]
    elif q == 'place that triggers ZERO_RESULTS':
        raise GeocoderError(GeocoderError.G_GEO_ZERO_RESULTS)
    else:
        raise Exception, u"Unexpected input to fake_geocoder: {}".format(q)

@attr(country='south_africa')
class HomeViewTest(TestCase):

    def test_homepage_context(self):
        response = self.client.get('/')
        self.assertIn('featured_mp', response.context)
        self.assertIn('news_articles', response.context)

@attr(country='south_africa')
class ConstituencyOfficesTestCase(WebTest):
    def setUp(self):
        self.old_HAYSTACK_SIGNAL_PROCESSOR = settings.HAYSTACK_SIGNAL_PROCESSOR
        settings.HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

        # Mapit Setup
        self.old_srid = settings.MAPIT_AREA_SRID
        settings.MAPIT_AREA_SRID = 4326

        self.generation = Generation.objects.create(
            active=True,
            description="Test generation",
            )

        self.province_type = Type.objects.create(
            code='PRV',
            description='Province',
            )

        self.mapit_test_province = Area.objects.create(
            name="Test Province",
            type=self.province_type,
            generation_low=self.generation,
            generation_high=self.generation,
            )

        self.mapit_test_province_shape = Geometry.objects.create(
            area=self.mapit_test_province,
            polygon=Polygon(((17, -29), (17, -30), (18, -30), (18, -29), (17, -29))),
            )
        # End of Mapit setup.

        (place_kind_province, _) = models.PlaceKind.objects.get_or_create(
            name='Province',
            slug='province',
            )

        models.Place.objects.create(
            name='Test Province',
            slug='test_province',
            kind=place_kind_province,
            mapit_area=self.mapit_test_province,
            )

        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        org_kind_constituency_office = models.OrganisationKind.objects.create(name='Constituency Office', slug='constituency-office')
        models.OrganisationKind.objects.create(name='Constituency Area', slug='constituency-area')

        party1 = models.Organisation.objects.create(name='Party1', slug='party1', kind=org_kind_party)
        party2 = models.Organisation.objects.create(name='Party2', slug='party2', kind=org_kind_party)

        p1_office1 = models.Organisation.objects.create(name='Party1: Office1', slug='party1-office1', kind=org_kind_constituency_office)
        p1_office2 = models.Organisation.objects.create(name='Party1: Office2', slug='party1-office2', kind=org_kind_constituency_office)
        p2_office1 = models.Organisation.objects.create(name='Party2: Office1', slug='party2-office1', kind=org_kind_constituency_office)
        p2_office2 = models.Organisation.objects.create(name='Party2: Office2', slug='party2-office2', kind=org_kind_constituency_office)

        orgrelkind_has_office = models.OrganisationRelationshipKind.objects.create(name='has_office')

        office_relationships = (
            (party1, p1_office1),
            (party1, p1_office2),
            (party2, p2_office1),
            (party2, p2_office2),
            )

        for party, office in office_relationships:
            models.OrganisationRelationship.objects.create(organisation_a=party, organisation_b=office, kind=orgrelkind_has_office)

        place_kind_constituency_office = models.PlaceKind.objects.create(name='Constituency Office', slug='constituency-office')
        models.PlaceKind.objects.create(name='Constituency Area', slug='constituency-area')


        # Offices inside the province
        models.Place.objects.create(
            name='Party1: Office1 Place',
            slug='party1-office1-place',
            kind=place_kind_constituency_office,
            location=Point(17.1, -29.1, srid=settings.MAPIT_AREA_SRID),
            organisation=p1_office1,
            )
        models.Place.objects.create(
            name='Party1: Office2 Place',
            slug='party1-office2-place',
            kind=place_kind_constituency_office,
            location=Point(17.2, -29.2, srid=settings.MAPIT_AREA_SRID),
            organisation=p1_office2,
            )
        models.Place.objects.create(
            name='Party2: Office1 Place',
            slug='party2-office1-place',
            kind=place_kind_constituency_office,
            location=Point(17.3, -29.3, srid=settings.MAPIT_AREA_SRID),
            organisation=p2_office1,
            )

        # This office is outside the province
        models.Place.objects.create(
            name='Party2: Office2 Place',
            slug='party2-office2-place',
            kind=place_kind_constituency_office,
            location=Point(16.9, -29, srid=settings.MAPIT_AREA_SRID),
            organisation=p2_office2,
            )


    def test_subplaces_page(self):
        response = self.app.get('/place/test_province/places/')

        content_boxes = response.html.findAll('div', {'class': 'content_box'})

        assert len(content_boxes) == 2, 'We should be seeing two groups of offices.'
        assert len(content_boxes[0].findAll('li')) == 2, 'Box 0 should contain two sections, each with a party office.'
        assert len(content_boxes[1].findAll('li')) == 1, 'Box 1 should contain one sections, as the other party office is outside the box.'

    def tearDown(self):
        settings.MAPIT_AREA_SRID = self.old_srid
        settings.HAYSTACK_SIGNAL_PROCESSOR = self.old_HAYSTACK_SIGNAL_PROCESSOR


@attr(country='south_africa')
class LatLonDetailViewTest(TestCase):
    def test_404_for_incorrect_province_lat_lon(self):
        res = self.client.get(reverse('latlon', kwargs={'lat': '0', 'lon': '0'}))
        self.assertEquals(404, res.status_code)


@attr(country='south_africa')
class SASearchViewTest(WebTest):

    def setUp(self):
        self.search_location_url = reverse('core_geocoder_search')
        self.search_url = reverse('core_search')

    def test_search_page_returns_success(self):
        res = self.app.get(reverse('core_search'))
        self.assertEquals(200, res.status_code)

    def test_invalid_date_range_params(self):
        response = self.app.get(
            "{0}?q=qwerty&start=invalid".format(self.search_url))
        range_controls = response.html.find(
            'div',
            class_='search-range-controls')
        date_start = range_controls.find('input', attrs={"name" : "start"})
        date_end = range_controls.find('input', attrs={"name" : "end"})
        self.assertEquals("", date_start["value"])
        self.assertEquals("", date_end["value"])

    def test_valid_date_start_param(self):
        response = self.app.get(
            "{0}?q=qwerty&start=2015-05-01".format(self.search_url))
        range_controls = response.html.find(
            'div',
            class_='search-range-controls')
        date_start = range_controls.find('input', attrs={"name" : "start"})
        date_end = range_controls.find('input', attrs={"name" : "end"})
        self.assertEquals("2015-05-01", date_start["value"])
        self.assertEquals("", date_end["value"])

    def test_valid_date_end_param(self,):
        response = self.app.get(
            "{0}?q=qwerty&end=2015-05-01".format(self.search_url))
        range_controls = response.html.find(
            'div',
            class_='search-range-controls')
        date_start = range_controls.find('input', attrs={"name" : "start"})
        date_end = range_controls.find('input', attrs={"name" : "end"})
        self.assertEquals("", date_start["value"])
        self.assertEquals("2015-05-01", date_end["value"])

    def get_search_result_list_items(self, query_string):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, query_string))
        results_div = response.html.find('div', class_='geocoded_results')
        return results_div.find('ul').findAll('li')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_unknown_place(self, mocked_geocoder):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, 'anywhere'))
        self.assertIsNone(
            response.html.find('div', class_='geocoded_results')
        )
        self.assertIn("No results for the location 'anywhere'", response)
        mocked_geocoder.assert_called_once_with(q='anywhere', country='za')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_zero_results_place(self, mocked_geocoder):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, 'place that triggers ZERO_RESULTS'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['geocoder_results'], [])
        results_div = response.html.find('div', class_='geocoded_results')
        self.assertIsNone(results_div)
        mocked_geocoder.assert_called_once_with(q='place that triggers ZERO_RESULTS', country='za')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_single_result_place(self, mocked_geocoder):
        response = self.app.get(
            "{0}?q={1}".format(self.search_location_url, 'Cape Town'))
        # If there's only a single result (as with Cape Town) we
        # should redirect straight there:
        self.assertEqual(response.status_code, 302)
        path = urlparse(response.location).path
        self.assertEqual(path, '/place/latlon/-33.925,18.424/')
        mocked_geocoder.assert_called_once_with(q='Cape Town', country='za')

    @patch('pombola.search.views.geocoder', side_effect=fake_geocoder)
    def test_multiple_result_place(self, mocked_geocoder):
        lis = self.get_search_result_list_items('Trafford Road')
        self.assertEqual(len(lis), 3)
        self.assertEqual(lis[0].a['href'], '/place/latlon/-29.814,30.839/')
        self.assertEqual(lis[1].a['href'], '/place/latlon/-33.969,18.703/')
        self.assertEqual(lis[2].a['href'], '/place/latlon/-32.982,27.868/')
        mocked_geocoder.assert_called_once_with(q='Trafford Road', country='za')


def connection_error(x, *args, **kwargs):
    print 'Raising connection error'
    raise requests.exceptions.ConnectionError


@attr(country='south_africa')
class SAPersonDetailViewTest(PersonSpeakerMappingsMixin, TestCase):
    def setUp(self):
        # Create the top level SayIt sections, so that there's no
        # warning when getting the person page:
        create_sections([{'heading': u"Hansard"},
                         {'heading': u"Committee Minutes"},
                         {'heading': u"Questions"}])

        moomin_finn = models.Person.objects.create(legal_name='Moomin Finn',
                                                   slug='moomin-finn')
        # Give moomin-finn a fake ID for the PMG API
        models.Identifier.objects.create(
            scheme='za.org.pmg.api/member',
            identifier=moomin_finn.slug,
            content_object=moomin_finn,
            )

        # Make sure there are SayIt speakers for all Pombola
        call_command('pombola_sayit_sync_pombola_to_popolo')

        # Put blank attendance data in the cache to stop us fetching from
        # the live PMG API
        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/member/moomin-finn/attendance/",
            [],
            )

    def _setup_positions_test_data(self):
        parliament = models.OrganisationKind.objects.create(
            name='Parliament',
            slug='parliament',
            )

        org = models.Organisation.objects.create(
            slug='national-assembly',
            name='National Assembly',
            kind=parliament,
            show_attendance=True
            )
        old_org = models.Organisation.objects.create(
            slug='old-assembly',
            name='Old Assembly',
            kind=parliament,
            )

        pt_member = models.PositionTitle.objects.create(
            slug='member', name='Member')
        pt_whip = models.PositionTitle.objects.create(
            slug='party-whip', name='Party Whip')

        person = models.Person.objects.get(slug='moomin-finn')
        person.position_set.create(
            title=pt_member, category='political', organisation=org,
        )
        person.position_set.create(
            title=pt_whip, category='political', organisation=org
        )
        person.position_set.create(
            title=pt_member, category='political', organisation=org,
            end_date=ApproximateDate(year=1999),
            )
        person.position_set.create(
            title=pt_member, category='political', organisation=old_org,
            end_date=ApproximateDate(year=1999),
            )
        person.position_set.create(
            title=pt_member, category='political', organisation=old_org,
            end_date=ApproximateDate(year=2000),
            )

    def test_unique_orgs_from_important_positions(self):
        self._setup_positions_test_data()

        c = Client()
        response = c.get('/person/moomin-finn/')
        self.assertContains(
            response,
            '<p><span class="position-title">National Assembly</span></p>',
            count=1,
            html=True,
        )

        self.assertContains(
            response,
            '<p>Formerly: <span class="position-title">Old Assembly</span></p>',
            count=1,
            html=True,
        )

    def test_person_to_speaker_resolution(self):
        person = models.Person.objects.get(slug='moomin-finn')
        speaker = self.pombola_person_to_sayit_speaker(person)
        self.assertEqual( speaker.name, 'Moomin Finn' )

    def test_generation_of_interests_table(self):
        #create data for the test
        person = models.Person.objects.get(slug=u'moomin-finn')

        category1 = Category.objects.create(name=u"Test Category", sort_order=1)
        category2 = Category.objects.create(name=u"Test Category 2", sort_order=2)

        release1 = Release.objects.create(name=u'2013', date=date(2013, 2, 16))
        Release.objects.create(name=u'2012', date=date(2012, 2, 24))

        entry1 = Entry.objects.create(person=person,release=release1,category=category1, sort_order=1)
        entry2 = Entry.objects.create(person=person,release=release1,category=category1, sort_order=2)
        entry3 = Entry.objects.create(person=person,release=release1,category=category2, sort_order=3)

        EntryLineItem.objects.create(entry=entry1,key=u'Field1',value=u'Value1')
        EntryLineItem.objects.create(entry=entry1,key=u'Field2',value=u'Value2')
        EntryLineItem.objects.create(entry=entry2,key=u'Field1',value=u'Value3')
        EntryLineItem.objects.create(entry=entry2,key=u'Field3',value=u'Value4')
        EntryLineItem.objects.create(entry=entry3,key=u'Field4',value=u'Value5')

        #actual output
        context = self.client.get(reverse('person', args=('moomin-finn',))).context

        #expected output
        expected = {
            1: {
                'name': u'2013',
                'categories': {
                    1: {
                        'name': u'Test Category',
                        'headings': [
                            u'Field1',
                            u'Field2',
                            u'Field3'
                        ],
                        'headingindex': {
                            u'Field1': 0,
                            u'Field2': 1,
                            u'Field3': 2
                        },
                        'headingcount': 4,
                        'entries': [
                            [
                                u'Value1',
                                u'Value2',
                                ''
                            ],
                            [
                                u'Value3',
                                '',
                                u'Value4'
                            ]
                        ]
                    },
                    2: {
                        'name': u'Test Category 2',
                        'headings': [
                            u'Field4'
                        ],
                        'headingindex': {
                            u'Field4': 0
                        },
                        'headingcount': 2,
                        'entries': [
                            [
                                u'Value5'
                            ]
                        ]
                    }
                }
            }
        }

        #ideally the following test would be run - however the ordering of entrylineitems appears to be somewhat unpredictable
        #self.assertEqual(context['interests'],expected)

        #determine key offsets as other tests may have added data to the database
        category_offset = context['interests'][0][0]['categories'].keys()[0]

        self.assertEqual(
            len(context['interests'][0][0]['categories'][category_offset]['headings']),
            len(expected[1]['categories'][1]['headings'])
        )
        self.assertEqual(
            len(context['interests'][0][0]['categories'][category_offset]['entries']),
            len(expected[1]['categories'][1]['entries'])
        )
        self.assertEqual(
            len(context['interests'][0][0]['categories'][category_offset]['entries'][0]),
            len(expected[1]['categories'][1]['entries'][0])
        )
        self.assertEqual(
            len(context['interests'][0][0]['categories'][category_offset+1]['headings']),
            len(expected[1]['categories'][2]['headings'])
        )
        self.assertEqual(
            len(context['interests'][0][0]['categories'][category_offset+1]['entries']),
            len(expected[1]['categories'][2]['entries'])
        )
        self.assertEqual(
            len(context['interests'][0][0]['categories'][category_offset+1]['entries'][0]),
            len(expected[1]['categories'][2]['entries'][0])
        )

    def _setup_party_for_attendance(self, show_attendance):
        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        party = models.Organisation.objects.create(name='Party', slug='party', kind=org_kind_party, show_attendance=show_attendance)
        person = models.Person.objects.get(slug='moomin-finn')
        positiontitle = models.PositionTitle.objects.create(name='Member', slug='member')
        models.Position.objects.create(person=person, organisation=party, title=positiontitle)

    def test_attendance_data(self):
        self._setup_party_for_attendance(True)
        test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data/test/attendance_587.json',
            )
        with open(test_data_path) as f:
            raw_data = json.load(f)

        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/member/moomin-finn/attendance/",
            raw_data['results'],
            )

        context = self.client.get(reverse('person', args=('moomin-finn',))).context

        self.assertEqual(
            context['attendance'],
            [{'total': 28, 'percentage': 89.28571428571429, 'attended': 25, 'year': 2015, 'position':'mp'},
             {'total': 15, 'percentage': 93.33333333333333, 'attended': 14, 'year': 2014, 'position':'mp'}],
            )

        self.assertEqual(
            context['latest_meetings_attended'],
            [{'url': 'https://pmg.org.za/committee-meeting/21460/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Performing Animals Protection Amendment Bill [B9-2015]: deliberations & finalisation; Plant Improvement [B8-2015] & Plant Breeders\u2019 Rights Bills [B11-2015]: Department response to Legal Advisor concerns',
              'date': datetime(2015, 9, 4).date()},
             {'url': 'https://pmg.org.za/committee-meeting/21374/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Performing Animals Protection Amendment Bill [B9-2015]: deliberations; Committee Support Officials on Plant Improvement Bill [B8-2015] and Plant Breeders\u2019 Rights Bill [B11-2015]',
              'date': datetime(2015, 8, 25).date()},
             {'url': 'https://pmg.org.za/committee-meeting/21327/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Department of Agriculture, Forestry and Fisheries 4th Quarter 2014/15 & 1st Quarter 2015/16 Performance',
              'date': datetime(2015, 8, 18).date()},
             {'url': 'https://pmg.org.za/committee-meeting/21268/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Performing Animals Protection Amendment Bill [B9-2015]: deliberations; Plant Improvement [B8-2015]  & Plant Breeders\u2019 Rights Bills[11-2015]: Department response to public inputs ',
              'date': datetime(2015, 8, 11).date()},
             {'url': 'https://pmg.org.za/committee-meeting/21141/',
              'committee_name': u'Rural Development and Land Reform',
              'title': u'One District-One Agri-Park implementation in context of Rural Economic Transformation Model',
              'date': datetime(2015, 6, 24).date()}],
            )

    @patch('requests.get', side_effect=connection_error)
    def test_attendance_data_requests_errors(self, m):
        self._setup_party_for_attendance(True)
        # Check context if identifier exists, cache lookup misses
        # and the PMG API is unavailable.
        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.clear()

        context = self.client.get(reverse('person', args=('moomin-finn',))).context
        assert context['attendance'] == 'UNAVAILABLE'

        # Get rid of identifiers so that we do the mocked url fetch
        # to find the identifier.
        models.Identifier.objects.all().delete()

        context = self.client.get(reverse('person', args=('moomin-finn',))).context
        assert context['attendance'] == 'UNAVAILABLE'

    def test_no_attendance_if_show_attendance_false(self):
        self._setup_party_for_attendance(False)
        test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data/test/attendance_587.json',
            )
        with open(test_data_path) as f:
            raw_data = json.load(f)

        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/member/moomin-finn/attendance/",
            raw_data['results'],
            )

        context = self.client.get(reverse('person', args=('moomin-finn',))).context

        self.assertEqual('attendance' in context, False)


    def _setup_example_positions(self, past, current):
        parliament = models.OrganisationKind.objects.create(
            name='Parliament',
            slug='parliament',
            )
        org = models.Organisation.objects.create(
            slug='national-assembly',
            name='National Assembly',
            kind=parliament,
            )
        pt_member = models.PositionTitle.objects.create(
            slug='member', name='Member')
        person = models.Person.objects.get(slug='moomin-finn')
        if current:
            person.position_set.create(
                title=pt_member, category='political', organisation=org,
            )
        if past:
            person.position_set.create(
                title=pt_member, category='political', organisation=org,
                start_date='2000-01-01', end_date='2005-12-31',
            )

    def test_no_past_no_current_positions(self):
        self._setup_example_positions(False, False)
        response = self.client.get(reverse('person', args=('moomin-finn',)))
        self.assertNotIn(
            '<a class="ui-tabs-anchor" href="#experience">Positions held</a>',
            response.content
        )
        self.assertNotIn(
            '<h3>Currently</h3>',
            response.content
        )
        self.assertNotIn(
            '<h3>Formerly</h3>',
            response.content
        )

    def test_past_and_current_positions(self):
        self._setup_example_positions(True, True)
        response = self.client.get(reverse('person', args=('moomin-finn',)))
        self.assertIn(
            '<a class="ui-tabs-anchor" href="#experience">Positions held</a>',
            response.content
        )
        self.assertIn(
            '<h3>Currently</h3>',
            response.content
        )
        self.assertRegexpMatches(
            response.content,
            r'Member\s+at <a href="/organisation/national-assembly/">National Assembly \(Parliament\)</a>\s*</li>'
        )
        self.assertIn(
            '<h3>Formerly</h3>',
            response.content
        )
        self.assertRegexpMatches(
            response.content,
            r'Member\s+at <a href="/organisation/national-assembly/">National Assembly \(Parliament\)</a>\s+from 1st January 2000\s+until 31st December 2005\s*</li>'
        )

    def test_past_but_no_current_positions(self):
        self._setup_example_positions(True, False)
        response = self.client.get(reverse('person', args=('moomin-finn',)))
        self.assertIn(
            '<a class="ui-tabs-anchor" href="#experience">Positions held</a>',
            response.content
        )
        self.assertIn(
            '<h3>Currently</h3>',
            response.content
        )
        self.assertIn(
            'No current positions recorded.',
            response.content
        )
        self.assertIn(
            '<h3>Formerly</h3>',
            response.content
        )
        self.assertRegexpMatches(
            response.content,
            r'Member\s+at <a href="/organisation/national-assembly/">National Assembly \(Parliament\)</a>\s+from 1st January 2000\s+until 31st December 2005\s*</li>'
        )

    def test_no_past_but_some_current_positions(self):
        self._setup_example_positions(False, True)
        response = self.client.get(reverse('person', args=('moomin-finn',)))
        self.assertIn(
            '<a class="ui-tabs-anchor" href="#experience">Positions held</a>',
            response.content
        )
        self.assertIn(
            '<h3>Currently</h3>',
            response.content
        )
        self.assertRegexpMatches(
            response.content,
            r'Member\s+at <a href="/organisation/national-assembly/">National Assembly \(Parliament\)</a>\s*</li>'
        )
        self.assertIn(
            '<h3>Formerly</h3>',
            response.content
        )
        self.assertIn(
            'No former positions recorded.',
            response.content
        )

    def test_email_sorting_by_preferred_without_wip(self):
        person = models.Person.objects.get(slug='moomin-finn')
        email_contact_kind = models.ContactKind.objects.create(name='Email', slug='email')
        person.contacts.create(kind=email_contact_kind, value='not-preferred@example.com', preferred=False)
        person.contacts.create(kind=email_contact_kind, value='preferred@example.com', preferred=True)

        response = self.client.get(reverse('person', args=('moomin-finn',)))
        self.assertIn(
            '<span class="email-address preferred"><a href="mailto:preferred@example.com">preferred@example.com</a></span>\n        \n          <span class="email-address"><a href="mailto:not-preferred@example.com">not-preferred@example.com</a></span>',
            response.content
        )

    def test_email_sorting_by_preferred_with_wip(self):
        person = models.Person.objects.get(slug='moomin-finn')
        email_contact_kind = models.ContactKind.objects.create(name='Email', slug='email')
        person.contacts.create(kind=email_contact_kind, value='not-preferred@example.com', preferred=False)
        person.contacts.create(kind=email_contact_kind, value='preferred@example.com', preferred=True)

        models.Identifier.objects.create(
            scheme='everypolitician',
            identifier='123456',
            content_object=person,
            )

        response = self.client.get(reverse('person', args=('moomin-finn',)))
        self.assertIn(
            '<li class="email-address preferred"><a href="mailto:preferred@example.com">preferred@example.com</a></li>\n        \n          <li class="email-address"><a href="mailto:not-preferred@example.com">not-preferred@example.com</a></li>',
            response.content
        )


@attr(country='south_africa')
class SAAttendanceDataTest(TestCase):
    def setUp(self):
        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        party1 = models.Organisation.objects.create(name='Party1', slug='party1', kind=org_kind_party)
        positiontitle1 = models.PositionTitle.objects.create(name='Member', slug='member')
        person1 = models.Person.objects.create(legal_name='Person1', slug='person1')
        models.Position.objects.create(person=person1, organisation=party1, title=positiontitle1)

        person2 = models.Person.objects.create(legal_name='Person2', slug='person2')
        positiontitle2 = models.PositionTitle.objects.create(name='Minister', slug='minister')
        models.Position.objects.create(person=person2, organisation=party1, title=positiontitle2, start_date='2015-08-01', end_date='future')

    def test_get_attendance_stats(self):
        raw_data = {
            2000: {
                'mp': {'A': 1, 'AP': 2, 'DE': 4, 'L': 8, 'LDE': 16, 'P': 32},
                'minister': {'A': 7, 'P': 48, 'L': 2, 'AP': 5}}
        }

        # Minister data expected first
        expected = [
            {'year': 2000,
            'attended': 50,
            'total': 62,
            'percentage': 100 * 50 / 62,
            'position': 'minister/deputy'},
            {'year': 2000,
            'attended': 60,
            'total': 63,
            'percentage': 100 * 60 / 63,
            'position': 'mp'},
        ]

        person = models.Person.objects.get(slug='person1')
        person_detail = SAPersonDetail(object = person)

        stats = person_detail.get_attendance_stats(raw_data)
        self.assertEqual(stats, expected)

        raw_data = {
            2000: {'mp': {'A': 1, 'P': 2}},
            2001: {'mp': {'A': 4, 'P': 8}},
            }

        expected = [
            {'year': 2001,
             'attended': 8,
             'total': 12,
             'percentage': 100 * 8 / 12,
             'position': 'mp',
             },
            {'year': 2000,
             'attended': 2,
             'total': 3,
             'percentage': 100 * 2 / 3,
             'position': 'mp',
             }
        ]

        stats = person_detail.get_attendance_stats(raw_data)
        self.assertEqual(stats, expected)

    def test_get_attendance_stats_raw(self):
        test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data/test/attendance_587.json',
            )
        with open(test_data_path) as f:
            raw_data = json.load(f)

        person = models.Person.objects.get(slug='person1')
        person_detail = SAPersonDetail(object = person)

        expected = {2014: {'mp': {u'A': 1, u'P': 14}}, 2015: {'mp': {u'A': 1, u'P': 25, u'AP': 2}}}
        raw_stats = person_detail.get_attendance_stats_raw(raw_data['results'])
        self.assertEqual(raw_stats, expected)

        # MP who has become a Minister
        person = models.Person.objects.get(slug='person2')
        person_detail = SAPersonDetail(object = person)

        expected = {2014: {'mp': {u'A': 1, u'P': 14}}, 2015: {'minister': {u'P': 4}, 'mp': {u'A': 1, u'P': 21, u'AP': 2}}}
        raw_stats = person_detail.get_attendance_stats_raw(raw_data['results'])
        self.assertEqual(raw_stats, expected)

    def test_get_meetings_attended(self):
        test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data/test/attendance_587.json',
            )
        with open(test_data_path) as f:
            raw_data = json.load(f)

        person = models.Person.objects.get(slug='person1')
        person_detail = SAPersonDetail(object = person)

        meetings_attended = person_detail.get_meetings_attended(raw_data['results'])
        meeting_keys = ['url', 'committee_name', 'summary', 'date', 'title']
        self.assertEqual(len(meetings_attended), 39)
        self.assertTrue(bool(k in meeting_keys for k in meetings_attended[0].iterkeys()))

@attr(country='south_africa')
class SAMpAttendancePageTest(TestCase):
    def setUp(self):
        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        party1 = models.Organisation.objects.create(name='Party1', slug='party1', kind=org_kind_party)
        positiontitle1 = models.PositionTitle.objects.create(name='Member', slug='member')
        person1 = models.Person.objects.create(legal_name='Person1', slug='person1')
        models.Position.objects.create(person=person1, organisation=party1, title=positiontitle1)

        self.person2 = models.Person.objects.create(legal_name='Person2', slug='person2', family_name='2', title='Dr', given_name='Person')
        positiontitle2 = models.PositionTitle.objects.create(name='Minister', slug='minister')
        models.Position.objects.create(person=self.person2, organisation=party1, title=positiontitle2, start_date='2000-03-30', end_date='future')
        # Needs to be a member of a party.
        models.Position.objects.create(person=self.person2, organisation=party1, title=positiontitle1)

        self.person3 = models.Person.objects.create(legal_name='Person3', slug='person3', family_name='3', given_name='Person')
        positiontitle3 = models.PositionTitle.objects.create(name='Deputy Minister of Something', slug='deputy-minister-of-something')
        models.Position.objects.create(person=self.person3, organisation=party1, title=positiontitle2, start_date='2000-01-01', end_date='2000-03-30')
        models.Position.objects.create(person=self.person3, organisation=party1, title=positiontitle3, start_date='2000-04-01', end_date='future')
        # Needs to be a member of a party.
        models.Position.objects.create(person=self.person3, organisation=party1, title=positiontitle1)

    def test_mp_attendance_context(self):
        raw_data = [{
            u'start_date': u'2000-01-01',
            u'end_date': u'2000-12-31',
            u'meetings_by_member': [
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person1/',
                    u'party_name': u'PARTY1', u'name': u'1, P', u'id': 1},
                 u'meetings': [
                    {u'date': u'2000-03-01', u'attendance': u'A'},
                    {u'date': u'2000-03-02', u'attendance': u'P'},
                    {u'date': u'2000-03-03', u'attendance': u'P'},
                    {u'date': u'2000-03-04', u'attendance': u'L'}]},
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person2/',
                    u'party_name': u'PARTY1', u'name': u'2, Dr P', u'id': 2},
                 u'meetings': [
                    {u'date': u'2000-03-01', u'attendance': u'A'},
                    {u'date': u'2000-03-01', u'attendance': u'P'},
                    {u'date': u'2000-04-01', u'attendance': u'P'},
                    {u'date': u'2000-04-01', u'attendance': u'P'},
                    {u'date': u'2000-04-01', u'attendance': u'A'}]},
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person3/',
                    u'party_name': u'PARTY1', u'name': u'3, P', u'id': 3},
                 u'meetings': [
                    {u'date': u'2000-03-01', u'attendance': u'P'},
                    {u'date': u'2000-04-01', u'attendance': u'P'},
                    {u'date': u'2000-04-01', u'attendance': u'P'},
                    {u'date': u'2000-04-01', u'attendance': u'A'}]}
            ],
        }]

        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/committee-meeting-attendance/meetings-by-member/",
            raw_data,
        )

        # Default, Minister attendance
        url = "%s?year=2000" % reverse('mp-attendance')
        context = self.client.get(url).context

        expected = [
            {'name': u'2, Dr P', 'pa_url': u'/person/person2/', 'party_name': u'PARTY1', 'present': 2, 'position': u'minister'},
            {'name': u'3, P', 'pa_url': u'/person/person3/', 'party_name': u'PARTY1', 'present': 3, 'position': u'deputy-minister'}]
        self.assertEqual(context['attendance_data'], expected)

        # MP attendance selected
        url = "%s?position=mps&year=2000" % reverse('mp-attendance')
        context = self.client.get(url).context

        # total: number of meetings
        # absent, arrived_late, depart_early, present: percentages
        expected = [
            {'name': u'1, P', 'party_name': u'PARTY1', 'pa_url': u'/person/person1/',
            'absent': 25, 'arrive_late': 25, 'depart_early': 0, 'total': 4, 'present': 75},
            {'name': u'2, Dr P', 'party_name': u'PARTY1', 'pa_url': u'/person/person2/',
            'absent': 50, 'arrive_late': 0, 'depart_early': 0, 'total': 2, 'present': 50}
        ]
        self.assertEqual(context['attendance_data'], expected)

    def test_some_attendance_as_mp_zero_attendance_as_minister(self):
        raw_data = [{
            u'end_date': u'2000-12-31',
            u'meetings_by_member': [
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person2/',
                    u'party_name': u'PARTY1', u'name': u'2, Dr P', u'id': 2},
                u'meetings': [
                    {u'date': u'2000-03-01', u'attendance': u'A'},
                    {u'date': u'2000-03-01', u'attendance': u'P'},]}],
            u'start_date': u'2000-01-01'}]

        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/committee-meeting-attendance/meetings-by-member/",
            raw_data,
        )

        url = "%s?year=2000" % reverse('mp-attendance')
        context = self.client.get(url).context

        # Zero attendance as a Minister
        expected = [
            {'name': u'2, Dr P', 'pa_url': u'/person/person2/', 'party_name': u'PARTY1', 'position': u'minister', 'present': 0},
            {'name': u'3, P', 'pa_url': u'/person/person3/', 'party_name': u'PARTY1', 'position': u'deputy-minister', 'present': 0}]
        self.assertEqual(context['attendance_data'], expected)

        # Some attendance as an MP
        url = "%s?position=mps&year=2000" % reverse('mp-attendance')
        context = self.client.get(url).context

        # total: number of meetings
        # absent, arrived_late, depart_early, present: percentages
        expected = [
            {'name': u'2, Dr P', 'party_name': u'PARTY1', 'pa_url': u'/person/person2/',
            'absent': 50, 'arrive_late': 0, 'depart_early': 0, 'total': 2, 'present': 50}
        ]
        self.assertEqual(context['attendance_data'], expected)

    def test_do_not_error_if_minister_has_no_parties(self):
        self.person2.position_set.filter(title__slug='member').delete()

        raw_data = [{
            u'end_date': u'2000-12-31',
            u'meetings_by_member': [
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person2/',
                    u'party_name': u'PARTY1', u'name': u'2, Dr P', u'id': 2},
                u'meetings': [
                    {u'date': u'2000-03-01', u'attendance': u'A'},
                    {u'date': u'2000-03-01', u'attendance': u'P'},]}],
            u'start_date': u'2000-01-01'}]

        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/committee-meeting-attendance/meetings-by-member/",
            raw_data,
        )

        url = "%s?year=2000" % reverse('mp-attendance')
        context = self.client.get(url).context

        # Zero attendance as a Minister
        expected = [
            {'name': u'2, Dr P', 'pa_url': u'/person/person2/', 'party_name': u'', 'position': u'minister', 'present': 0},
            {'name': u'3, P', 'pa_url': u'/person/person3/', 'party_name': u'PARTY1', 'position': u'deputy-minister', 'present': 0}]
        self.assertEqual(context['attendance_data'], expected)


        # When filtered by party, only display ministers with active memberships
        url = "%s?year=2000&party=PARTY1" % reverse('mp-attendance')
        context = self.client.get(url).context

        expected = [
            {'name': u'3, P', 'pa_url': u'/person/person3/', 'party_name': u'PARTY1', 'position': u'deputy-minister', 'present': 0}]
        self.assertEqual(context['attendance_data'], expected)


    def test_divide_2019_attendance_records_pre_and_post_elections(self):
        # Pre election: 01/01/2019 - 30/06/2019
        # Post election: 01/07/2019 - 31/12/2019

        raw_data = [{
            u'start_date': u'2019-01-01',
            u'end_date': u'2019-12-31',
            u'meetings_by_member': [
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person2/',
                    u'party_name': u'PARTY1', u'name': u'2, Dr P', u'id': 2},
                u'meetings': [
                    {u'date': u'2019-01-01', u'attendance': u'A'},
                    {u'date': u'2019-06-30', u'attendance': u'P'},
                    {u'date': u'2019-07-01', u'attendance': u'P'},
                    {u'date': u'2019-12-31', u'attendance': u'P'},]},
                {u'member': {
                    u'party_id': 1, u'pa_url': u'http://www.pa.org.za/person/person3/',
                    u'party_name': u'PARTY1', u'name': u'3, P', u'id': 3},
                u'meetings': [
                    {u'date': u'2019-07-01', u'attendance': u'P'}]}]
            }]

        pmg_api_cache = caches['pmg_api']
        pmg_api_cache.set(
            "https://api.pmg.org.za/committee-meeting-attendance/meetings-by-member/",
            raw_data,
        )

        url = "%s?year=2019" % reverse('mp-attendance')
        context = self.client.get(url).context

        expected = [
            {'name': u'2, Dr P', 'pa_url': u'/person/person2/', 'party_name': u'PARTY1', 'position': u'minister', 'present': 1},
            {'name': u'3, P', 'pa_url': u'/person/person3/', 'party_name': u'PARTY1', 'position': u'deputy-minister', 'present': 0}]

        self.assertEqual(context['attendance_data'], expected)

        url = "%s?year=2019+-+post+elections" % reverse('mp-attendance')
        context = self.client.get(url).context

        expected = [
            {'name': u'2, Dr P', 'pa_url': u'/person/person2/', 'party_name': u'PARTY1', 'position': u'minister', 'present': 2},
            {'name': u'3, P', 'pa_url': u'/person/person3/', 'party_name': u'PARTY1', 'position': u'deputy-minister', 'present': 1}]

        self.assertEqual(context['attendance_data'], expected)


@attr(country='south_africa')
class SAPersonProfileSubPageTest(WebTest):
    def setUp(self):
        self.org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        self.org_kind_parliament = models.OrganisationKind.objects.create(name='Parliament', slug='parliament')
        self.membership = models.PositionTitle.objects.create(name='Member', slug='member')
        self.post = models.PositionTitle.objects.create(name='Speaker', slug='speaker')
        self.party = models.Organisation(
            name = 'Test Party',
            slug = 'test-party',
            kind = self.org_kind_party,
        )
        self.party.save()
        self.parliament = models.Organisation(
            name = 'National Assembly',
            slug = 'national-assembly',
            kind = self.org_kind_parliament,
        )
        self.parliament.save()

        self.deceased = models.Person.objects.create(
            legal_name="Deceased Person",
            slug='deceased-person',
            date_of_birth='1965-12-31',
            date_of_death='2010-01-01',
        )
        self.deceased.position_set.create(
            title=self.membership,
            organisation=self.party,
            category='political',
            start_date='2008-12-12',
            end_date='2010-01-01',
        )
        self.deceased.position_set.create(
            title=self.membership,
            organisation=self.parliament,
            category='political',
            start_date='2008-04-01',
            end_date='2010-01-01',
        )
        self.deceased.position_set.create(
            title=self.post,
            organisation=self.parliament,
            category='political',
            start_date='2008-04-01',
            end_date='2010-01-01',
        )

        self.former_mp = models.Person.objects.create(
            legal_name="Former MP",
            slug='former-mp',
        )
        self.former_mp.position_set.create(
            title=self.membership,
            organisation=self.party,
            category='political',
            start_date='2010-01-02',
            end_date='future',
        )
        self.former_mp.position_set.create(
            title=self.membership,
            organisation=self.parliament,
            category='political',
            start_date='2010-04-01',
            end_date='2014-04-01',
        )

        # Make some identifiers for these people so we avoid
        # looking them up with PMG, and put blank attendance data
        # in the cache to stop us fetching from the live PMG API.
        pmg_api_cache = caches['pmg_api']

        for person in (self.deceased, self.former_mp):
            models.Identifier.objects.create(
                scheme='za.org.pmg.api/member',
                identifier=person.slug,
                content_object=person,
                )

            pmg_api_cache.set(
                "https://api.pmg.org.za/member/{}/attendance/".format(person.slug),
                [],
                )


    def get_person_summary(self, soup):
        return soup.find('div', class_='person-summary')

    def get_positions_tab(self, soup):
        return soup.find('div', id='experience')

    def get_profile_info(self, soup):
        return soup.find('div', class_='profile-info')

    def test_person_death_date(self):
        response = self.app.get('/person/deceased-person/')
        summary = self.get_person_summary(response.html)

        self.assertEqual(summary.findNext('p').contents[0], 'Died 1st January 2010')

    def test_deceased_party_affiliation(self):
        response = self.app.get('/person/deceased-person/')
        sidebar = self.get_profile_info(response.html)
        party_heading = sidebar.findNext('div', class_='constituency-party')
        party_name = party_heading.findNext('h3', text='Party').findNextSibling('ul').text

        self.assertEqual(party_name.strip(), 'Test Party')

    def test_deceased_former_positions(self):
        response = self.app.get('/person/deceased-person/')
        profile_tab = self.get_positions_tab(response.html)

        former_pos_heading = profile_tab.findNext('h3', text='Formerly')
        former_pos_list = former_pos_heading.findNextSibling('ul').text

        self.assertNotEqual(former_pos_heading, None)

        # check for the former MP and Speaker positions
        self.assertRegexpMatches(former_pos_list, r'Member\s+at National Assembly \(Parliament\)')
        self.assertRegexpMatches(former_pos_list, r'Speaker\s+at National Assembly \(Parliament\)')

    def test_former_mp(self):
        response = self.app.get('/person/former-mp/')
        positions_tab = self.get_positions_tab(response.html)
        former_pos_heading = positions_tab.findNext('h3', text='Formerly')
        former_pos_list = former_pos_heading.findNextSibling('ul').text

        self.assertNotEqual(former_pos_heading, None)

        self.assertRegexpMatches(former_pos_list, r'Member\s+at National Assembly \(Parliament\)')


@attr(country='south_africa')
class SAOrganisationPartySubPageTest(TestCase):

    def setUp(self):
        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        org_kind_parliament = models.OrganisationKind.objects.create(name='Parliament', slug='parliament')

        party1 = models.Organisation.objects.create(name='Party1', slug='party1', kind=org_kind_party)
        party2 = models.Organisation.objects.create(name='Party2', slug='party2', kind=org_kind_party)
        house1 = models.Organisation.objects.create(name='House1', slug='house1', kind=org_kind_parliament)

        positiontitle1 = models.PositionTitle.objects.create(name='Member', slug='member')
        positiontitle2 = models.PositionTitle.objects.create(name='Delegate', slug='delegate')
        positiontitle3 = models.PositionTitle.objects.create(name='Whip', slug='whip')

        person1 = models.Person.objects.create(legal_name='Person1', slug='person1')
        person2 = models.Person.objects.create(legal_name='Person2', slug='person2')
        person3 = models.Person.objects.create(legal_name='Person3', slug='person3')
        person4 = models.Person.objects.create(legal_name='Person4', slug='person4')
        person5 = models.Person.objects.create(legal_name='Person5', slug='person5')
        person6 = models.Person.objects.create(legal_name='', slug='empty-legal-name')

        models.Position.objects.create(person=person1, organisation=party1, title=positiontitle1)
        models.Position.objects.create(person=person2, organisation=party1, title=positiontitle1)
        models.Position.objects.create(person=person3, organisation=party1, title=positiontitle1)
        models.Position.objects.create(person=person4, organisation=party2, title=positiontitle1)
        models.Position.objects.create(person=person5, organisation=party2, title=positiontitle2)

        models.Position.objects.create(person=person1, organisation=house1, title=positiontitle1)
        models.Position.objects.create(person=person2, organisation=house1, title=positiontitle1)
        models.Position.objects.create(person=person3, organisation=house1, title=positiontitle1, end_date='2013-02-16')
        models.Position.objects.create(person=person4, organisation=house1, title=positiontitle1)
        models.Position.objects.create(person=person5, organisation=house1, title=positiontitle1, end_date='2013-02-16')

        # Add a position for the person with an empty legal name,
        # since this isn't prevented by any validation:
        models.Position.objects.create(person=person6, organisation=party1, title=positiontitle1)
        models.Position.objects.create(person=person6, organisation=house1, title=positiontitle1)

        #check for person who is no longer an official, but still a member
        models.Position.objects.create(person=person1, organisation=house1, title=positiontitle3, end_date='2013-02-16')

    def test_display_current_members(self):
        context1 = self.client.get(reverse('organisation_party', args=('house1', 'party1'))).context
        context2 = self.client.get(reverse('organisation_party', args=('house1', 'party2'))).context

        expected1 = ['<Position:  (Member at House1)>', '<Position: Person1 (Member at House1)>', '<Position: Person2 (Member at House1)>']
        expected2 = ['<Position: Person4 (Member at House1)>']

        self.assertQuerysetEqual(context1['sorted_positions'], expected1)
        self.assertQuerysetEqual(context2['sorted_positions'], expected2)
        self.assertEqual(context1['sorted_positions'][0].person.slug, 'empty-legal-name')
        self.assertEqual(context1['sorted_positions'][1].person.slug, 'person1')
        self.assertEqual(context1['sorted_positions'][2].person.slug, 'person2')
        self.assertEqual(context2['sorted_positions'][0].person.slug, 'person4')

    def test_display_past_members(self):
        context1 = self.client.get(reverse('organisation_party', args=('house1', 'party1')), {'historic': '1'}).context
        context2 = self.client.get(reverse('organisation_party', args=('house1', 'party2')), {'historic': '1'}).context

        expected1 = ['<Position: Person3 (Member at House1)>']
        expected2 = ['<Position: Person5 (Member at House1)>']

        self.assertQuerysetEqual(context1['sorted_positions'], expected1)
        self.assertQuerysetEqual(context2['sorted_positions'], expected2)
        self.assertEqual(context1['sorted_positions'][0].person.slug, 'person3')
        self.assertEqual(context2['sorted_positions'][0].person.slug, 'person5')

    def test_display_all_members(self):
        context1 = self.client.get(reverse('organisation_party', args=('house1', 'party1')), {'all': '1'}).context
        context2 = self.client.get(reverse('organisation_party', args=('house1', 'party2')), {'all': '1'}).context

        expected1 = ['<Position:  (Member at House1)>','<Position: Person1 (Member at House1)>','<Position: Person1 (Whip at House1)>','<Position: Person2 (Member at House1)>','<Position: Person3 (Member at House1)>']
        expected2 = ['<Position: Person4 (Member at House1)>','<Position: Person5 (Member at House1)>']

        self.assertQuerysetEqual(context1['sorted_positions'], expected1)
        self.assertQuerysetEqual(context2['sorted_positions'], expected2)
        self.assertEqual(context1['sorted_positions'][0].person.slug, 'empty-legal-name')
        self.assertEqual(context1['sorted_positions'][1].person.slug, 'person1')
        self.assertEqual(context1['sorted_positions'][2].person.slug, 'person1')
        self.assertEqual(context1['sorted_positions'][3].person.slug, 'person2')
        self.assertEqual(context1['sorted_positions'][4].person.slug, 'person3')
        self.assertEqual(context2['sorted_positions'][0].person.slug, 'person4')
        self.assertEqual(context2['sorted_positions'][1].person.slug, 'person5')


@attr(country='south_africa')
class SAOrganisationPeopleSubPageTest(TestCase):

    def setUp(self):
        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        org_kind_parliament = models.OrganisationKind.objects.create(name='Parliament', slug='parliament')

        ncop = models.Organisation.objects.create(name='NCOP', slug='ncop', kind=org_kind_parliament)

        whip = models.PositionTitle.objects.create(name='Whip', slug='whip')
        delegate = models.PositionTitle.objects.create(name='Delegate', slug='delegate')

        aardvark = models.Person.objects.create(legal_name='Anthony Aardvark', slug='aaardvark')
        alice = models.Person.objects.create(legal_name='Alice Smith', slug='asmith')
        bob = models.Person.objects.create(legal_name='Bob Smith', slug='bsmith')
        charlie = models.Person.objects.create(legal_name='Charlie Bucket', slug='cbucket')
        zebra = models.Person.objects.create(legal_name='Zoe Zebra', slug='zzebra')
        anon = models.Person.objects.create(legal_name='', slug='anon')

        self.aardvark_ncop = aardvark_ncop= models.Position.objects.create(person=aardvark, organisation=ncop, title=delegate)
        self.alice_ncop = alice_ncop = models.Position.objects.create(person=alice, organisation=ncop, title=delegate)
        self.bob_ncop = bob_ncop = models.Position.objects.create(person=bob, organisation=ncop, title=delegate)
        self.alice_ncop_whip = alice_ncop_whip = models.Position.objects.create(person=alice, organisation=ncop, title=whip)
        self.zebra_ncop = zebra_ncop = models.Position.objects.create(person=zebra, organisation=ncop, title=delegate)
        self.anon_ncop = models.Position.objects.create(person=anon, organisation=ncop, title=delegate)

        self.charlie_ncop = models.Position.objects.create(person=charlie, organisation=ncop, title=None)

    def test_members_with_same_surname(self):
        context = self.client.get(reverse('organisation_people', kwargs={'slug': 'ncop'})).context

        expected = [
            x.id for x in
            (
                # First any positions of people with blank legal_name
                self.anon_ncop,
                # Then alphabetical order by 'surname'
                self.aardvark_ncop,
                # This should happen even if the person has a missing title
                self.charlie_ncop,
                # Inside alphabetical order, positions for the same person should be grouped
                # by person with the parliamentary membership first
                self.alice_ncop, self.alice_ncop_whip,
                self.bob_ncop,
                # Surnames beginning with Z should be at the end
                self.zebra_ncop,
                )
            ]

        self.assertEqual([x.id for x in context['sorted_positions']], expected)

    def test_fetch_single_letter(self):
        context = self.client.get(
            reverse(
                'organisation_people_prefix',
                kwargs={'slug': 'ncop', 'person_prefix': 'A'},
                )
            ).context

        expected_positions = [self.aardvark_ncop.id]
        self.assertEqual([x.id for x in context['sorted_positions']], expected_positions)

        self.assertEqual(context['current_name_prefix'], 'A')

        expected_count_by_prefix = [
            ('A', 1),
            ('B', 1),
            ('C', 0),
            ('D', 0),
            ('E', 0),
            ('F', 0),
            ('G', 0),
            ('H', 0),
            ('I', 0),
            ('J', 0),
            ('K', 0),
            ('L', 0),
            ('M', 0),
            ('N', 0),
            ('O', 0),
            ('P', 0),
            ('Q', 0),
            ('R', 0),
            ('S', 3),
            ('T', 0),
            ('U', 0),
            ('V', 0),
            ('W', 0),
            ('X', 0),
            ('Y', 0),
            ('Z', 1),
        ]
        self.assertEqual(context['count_by_prefix'], expected_count_by_prefix)


@attr(country='south_africa')
class SAHansardIndexViewTest(TestCase):

    def setUp(self):
        create_sections([
            {
                'heading': u"Hansard",
                'subsections': [
                    {   'heading': u"2013",
                        'subsections': [
                            {   'heading': u"02",
                                'subsections': [
                                    {   'heading': u"16",
                                        'subsections': [
                                            {   'heading': u"Proceedings of the National Assembly (2012/2/16)",
                                                'subsections': [
                                                    {   'heading': u"Proceedings of Foo",
                                                        'speeches': [ 4, date(2013, 2, 16), time(9, 0) ],
                                                    },
                                                    {   'heading': u"Bill on Silly Walks",
                                                        'speeches': [ 2, date(2013, 2, 16), time(12, 0) ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                    {
                                        'heading': u"18",
                                        'subsections': [
                                            {   'heading': u"Proceedings of the National Assembly (2012/2/18)",
                                                'subsections': [
                                                    {   'heading': u"Budget Report",
                                                        'speeches': [ 3, date(2013, 2, 18), time(9, 0) ],
                                                    },
                                                    {   'heading': u"Bill on Comedy Mustaches",
                                                        'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                'heading': u"Empty section",
                            }
                        ],
                    },
                ],
            },
        ])

    def test_index_page(self):
        c = Client()
        response = c.get('/hansard/')
        self.assertEqual(response.status_code, 200)

        section_name = "Proceedings of Foo"
        section = Section.objects.get(heading=section_name)

        # Check that we can see the headings of sections containing speeches only
        self.assertContains(response, section_name)
        self.assertContains(response, '<a href="/%s">%s</a>' % (section.get_path, section_name), html=True)
        self.assertNotContains(response, "Empty section")

@attr(country='south_africa')
class SACommitteeIndexViewTest(WebTest):

    def setUp(self):
        self.fish_section_heading = u"Oh fishy fishy fishy fishy fishy fish"
        self.forest_section_heading = u"Forests are totes awesome"
        self.pmq_section_heading = "Questions on 20 June 2014"
        # Make sure that the default SayIt instance exists
        default_instance, _ = Instance.objects.get_or_create(label='default')
        create_sections([
            {
                'heading': u"Committee Minutes",
                'subsections': [
                    {   'heading': u"Agriculture, Forestry and Fisheries",
                        'subsections': [
                            {   'heading': u"16 November 2012",
                                'subsections': [
                                    {   'heading': self.fish_section_heading,
                                        'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
                                    },
                                    {
                                        'heading': u"Empty section",
                                    }
                                ],
                            },
                            {   'heading': "17 November 2012",
                                'subsections': [
                                    {   'heading': self.forest_section_heading,
                                        'speeches': [ 7, date(2013, 2, 19), time(9, 0), False ],
                                    },
                                    {
                                        'heading': "Empty section",
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'heading': u"Hansard",
                'subsections': [
                    {   'heading': u"Prime Minister's Questions",
                        'subsections': [
                            {   'heading': self.pmq_section_heading,
                                'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
                            },
                        ],
                    },
                ],
            },
        ], instance=default_instance)

    def test_committee_index_page(self):
        response = self.app.get('/committee-minutes/')
        self.assertEqual(response.status_code, 200)

        section = Section.objects.get(heading=self.fish_section_heading)

        # Check that we can see the headings of sections containing speeches only
        self.assertContains(response, "16 November 2012")
        self.assertContains(response, self.fish_section_heading)
        self.assertContains(response,
                            '<a href="/%s">%s</a>' % (section.get_path,
                                                      self.fish_section_heading),
                            html=True)
        self.assertNotContains(response, "Empty section")

    def test_committee_section_redirects(self):
        # Get the section URL:
        section = Section.objects.get(heading=self.fish_section_heading)
        section_url = reverse('speeches:section-view', args=(section.get_path,))
        response = self.app.get(section_url)
        self.assertEqual(response.status_code, 302)
        url_match = re.search(r'http://somewhere.or.other/\d+',
                              response.location)
        self.assertTrue(url_match)

    def view_speech_in_section(self, section_heading):
        section = Section.objects.get(heading=section_heading)
        # Pick an arbitrary speech in that section:
        speech = Speech.objects.filter(section=section)[0]
        speech_url = reverse('speeches:speech-view', args=(speech.id,))
        # Get that URL, and expect to see a redirect to the source_url:
        return self.app.get(speech_url)

    def check_redirect(self, response):
        self.assertEqual(response.status_code, 302)
        url_match = re.search(r'http://somewhere.or.other/\d+',
                              response.location)
        self.assertTrue(url_match)

    def test_public_committee_speech_redirects(self):
        # Try a speech in a section that contains private speeches:
        self.check_redirect(self.view_speech_in_section(self.fish_section_heading))

    def test_private_committee_speech_redirects(self):
        # Try a speech in a section that contains public speeches:
        self.check_redirect(self.view_speech_in_section(self.forest_section_heading))

    def test_hansard_speech_returned(self):
        response = self.view_speech_in_section(self.pmq_section_heading)
        self.assertEqual(response.status_code, 200)
        self.assertIn('rhubarb rhubarb', response)

@attr(country='south_africa')
class SAOrganisationDetailViewTest(WebTest):

    def setUp(self):
        # Create a test organisation and some associated models
        person = models.Person.objects.create(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )

        person2 = models.Person.objects.create(
            legal_name = 'Zest ABCPerson',
            slug       = 'zest-abcperson',
        )

        organisation_kind = models.OrganisationKind.objects.create(
            name = 'Foo',
            slug = 'foo',
        )

        organisation = models.Organisation.objects.create(
            name = 'Test Org',
            slug = 'test-org',
            kind = organisation_kind,
        )

        title = models.PositionTitle.objects.create(
            name = 'Test title',
            slug = 'test-title',
        )

        models.Position.objects.create(
            person = person,
            title  = title,
            organisation = organisation,
        )

        models.Position.objects.create(
            person = person2,
            title  = title,
            organisation = organisation,
        )

    def test_ordering_of_positions(self):
        # We expect the positions to be sorted by the "last name" of the
        # people in them.
        resp = self.app.get('/organisation/test-org/')
        positions = resp.context['positions']
        self.assertEqual(positions[0].person.legal_name, "Zest ABCPerson")
        self.assertEqual(positions[1].person.legal_name, "Test Person")


@attr(country='south_africa')
class SAOrganisationDetailViewWriteInPublicTest(TestCase):
    def setUp(self):
        na_committee_kind = models.OrganisationKind.objects.create(name='National Assembly Committees', slug='national-assembly-committees')
        self.committee = models.Organisation.objects.create(slug='test-committee', kind=na_committee_kind)

    def test_not_contactable_via_writeinpublic_with_no_email(self):
        response = self.client.get(reverse('organisation', kwargs={'slug': self.committee.slug}))
        self.assertFalse(response.context['contactable_via_writeinpublic'])

    def test_contactable_via_writeinpublic_with_email(self):
        email_contact_kind = models.ContactKind.objects.create(name='Email', slug='email')
        self.committee.contacts.create(kind=email_contact_kind, value='test@example.com', preferred=False)
        response = self.client.get(reverse('organisation', kwargs={'slug': self.committee.slug}))
        self.assertTrue(response.context['contactable_via_writeinpublic'])

    def test_contactable_via_writeinpublic_not_committee(self):
        org_kind = models.OrganisationKind.objects.create(name='Test', slug='test')
        org = models.Organisation.objects.create(slug='test-org', kind=org_kind)
        response = self.client.get(reverse('organisation', kwargs={'slug': org.slug}))
        self.assertFalse(response.context['contactable_via_writeinpublic'])


@attr(country='south_africa')
class SAOrganisationDetailViewTestParliament(WebTest):

    def setUp(self):
        # We create a small model parliament here - this includes:
        #  - Current Speaker Jane Doe (Random Party)
        #  - Current MP Joe Bloggs (used to be in Now Defunct Party,
        #    now in Another Random Party)
        #  - Current MP John Smith (Another Random Party)
        #  - Past MP Old MP (used to be in the Monster Raving Loony Party)
        # This exercises a few awkward cases when calculating the
        # proportions of each party within the parliament - this should
        # be presented as 66% Another Random Party, 33% Random Party.
        self.parliament_kind = models.OrganisationKind.objects.create(
            name='Parliament',
            slug='parliament')
        self.party_kind = models.OrganisationKind.objects.create(
            name='Party',
            slug='party')
        self.organisation = models.Organisation.objects.create(
            kind=self.parliament_kind,
            name='Model Parliament',
            slug='model-parliament')
        self.party_random = models.Organisation.objects.create(
            kind=self.party_kind,
            name='Random Party',
            slug='random-party')
        self.party_another_random = models.Organisation.objects.create(
            kind=self.party_kind,
            name='Another Random Party',
            slug='another-random-party')
        self.party_defunct = models.Organisation.objects.create(
            kind=self.party_kind,
            name='Now Defunct Party',
            slug='now-defunct-party')
        self.party_loony = models.Organisation.objects.create(
            kind=self.party_kind,
            name='Monster Raving Loony Party',
            slug='monster-raving-loony-party')
        self.person = models.Person.objects.create(
            legal_name='Joe Bloggs',
            slug='joe-bloggs')
        self.member_title = models.PositionTitle.objects.create(
            name='Member',
            slug='member')
        self.speaker_title = models.PositionTitle.objects.create(
            name='Speaker',
            slug='speaker')
        self.position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.old_party_position = models.Position.objects.create(
            person=self.person,
            organisation=self.party_defunct,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(2002, 12, 31),
        )
        self.party_position = models.Position.objects.create(
            person=self.person,
            organisation=self.party_another_random,
            title=self.member_title,
            start_date=ApproximateDate(2003, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.person2 = models.Person.objects.create(
            legal_name='John Smith',
            slug='john-smith',
        )
        self.position2 = models.Position.objects.create(
            person=self.person2,
            organisation=self.organisation,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.party_position2 = models.Position.objects.create(
            person=self.person2,
            organisation=self.party_another_random,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.speaker = models.Person.objects.create(
            legal_name='Jane Doe',
            slug='jane-doe',
        )
        self.speaker_position = models.Position.objects.create(
            person=self.speaker,
            organisation=self.organisation,
            title=self.speaker_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.speaker_party_position = models.Position.objects.create(
            person=self.speaker,
            organisation=self.party_random,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.old_mp = models.Person.objects.create(
            legal_name='Old MP',
            slug='old-mp'
        )
        self.old_mp_position = models.Position.objects.create(
            person=self.old_mp,
            organisation=self.organisation,
            title=self.member_title,
            start_date=ApproximateDate(2001, 1, 1),
            end_date=ApproximateDate(2002, 12, 31),
        )
        self.old_mp_party_position = models.Position.objects.create(
            person=self.old_mp,
            organisation=self.party_loony,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(2005, 12, 31),
        )

    def test_counts_and_percentages(self):
        with self.assertNumQueries(13):
            response = self.app.get('/organisation/model-parliament/')
        ps_and_ps = response.context['parties_counts_and_percentages']
        self.assertEqual(2, len(ps_and_ps))
        self.assertEqual(ps_and_ps[0][0], self.party_another_random)
        self.assertEqual(ps_and_ps[0][1], 2)
        self.assertAlmostEqual(ps_and_ps[0][2], 66.666666666666)
        self.assertEqual(ps_and_ps[1][0], self.party_random)
        self.assertEqual(ps_and_ps[1][1], 1)
        self.assertAlmostEqual(ps_and_ps[1][2], 33.333333333333)

@attr(country='south_africa')
class SAOrganisationDetailViewTestPlaceAndTitleDisplay(WebTest):

    def setUp(self):
        placekind = models.PlaceKind.objects.create(
            name='Test Place Kind',
            slug='test-place-kind',
        )
        self.place = models.Place.objects.create(
            name='Test Place',
            slug='test-place',
            kind=placekind,
        )
        self.parliament_kind = models.OrganisationKind.objects.create(
            name='Parliament',
            slug='parliament')
        self.party_kind = models.OrganisationKind.objects.create(
            name='Party',
            slug='party')
        self.organisation = models.Organisation.objects.create(
            kind=self.parliament_kind,
            name='National Assembly',
            slug='national-assembly')
        self.other_organisation = models.Organisation.objects.create(
            kind=self.parliament_kind,
            name='Another Assembly',
            slug='another-assembly')
        self.ncop = models.Organisation.objects.create(
            kind=self.parliament_kind,
            name='National Council of Provinces',
            slug='ncop')
        self.party_random = models.Organisation.objects.create(
            kind=self.party_kind,
            name='Random Party',
            slug='random-party')
        self.party_another_random = models.Organisation.objects.create(
            kind=self.party_kind,
            name='Another Random Party',
            slug='another-random-party')
        self.person = models.Person.objects.create(
            legal_name='Joe Bloggs',
            slug='joe-bloggs')
        self.person2 = models.Person.objects.create(
            legal_name='Adam Smith',
            slug='adam-smith')
        self.person3 = models.Person.objects.create(
            legal_name='John Smith',
            slug='john-smith')
        self.member_title = models.PositionTitle.objects.create(
            name='Member',
            slug='member')
        self.speaker_title = models.PositionTitle.objects.create(
            name='Speaker',
            slug='speaker')
        self.position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            title=self.member_title,
            place=self.place,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.position2 = models.Position.objects.create(
            person=self.person2,
            organisation=self.other_organisation,
            title=self.member_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.position3 = models.Position.objects.create(
            person=self.person3,
            organisation=self.ncop,
            title=self.member_title,
            place=self.place,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )
        self.speaker_position = models.Position.objects.create(
            person=self.person,
            organisation=self.organisation,
            title=self.speaker_title,
            start_date=ApproximateDate(2000, 1, 1),
            end_date=ApproximateDate(future=True),
        )

    def test_positions(self):
        response = self.app.get('/organisation/national-assembly/people/')

        self.assertNotRegexpMatches(
            str(response.html.find(class_='list-of-people').find('li')),
            r'Member'
        )

        self.assertRegexpMatches(
            str(response.html.find(class_='list-of-people').find('li')),
            r'Speaker'
        )

        response = self.app.get('/organisation/another-assembly/people/')
        self.assertRegexpMatches(
            str(response.html.find(class_='list-of-people').find('li')),
            r'Member'
        )

    def test_places(self):
        response = self.app.get('/organisation/national-assembly/people/')
        self.assertNotRegexpMatches(
            str(response.html.find(class_='list-of-people').find('li')),
            r'Test Place'
        )

        response = self.app.get('/organisation/ncop/people/')
        self.assertRegexpMatches(
            str(response.html.find(class_='list-of-people').find('li')),
            r'Test Place'
        )


@attr(country='south_africa')
class SAPlaceDetailViewTest(WebTest):

    def setUp(self):

        # Create a test place

        placekind = models.PlaceKind.objects.create(
            name='Test Place Kind',
            slug='test-place-kind',
        )

        self.place = models.Place.objects.create(
            name='Test Place',
            slug='test-place',
            kind=placekind,
        )

        # Create test organisation kinds

        orgkind = models.OrganisationKind.objects.create(
            name='Test OrganisationKind',
            slug='test-orgkind',
        )

        orgkind_legislature = models.OrganisationKind.objects.create(
            name='Test OrganisationKind Legislature',
            slug='provincial-legislature',
        )

        # Create test organisations

        self.org_assembly = models.Organisation.objects.create(
            name='Test Organisation Assembly',
            slug='national-assembly',
            kind=orgkind,
        )

        self.org_ncop = models.Organisation.objects.create(
            name='Test Organisation NCOP',
            slug='ncop',
            kind=orgkind,
        )

        self.org_legislature = models.Organisation.objects.create(
            name='Test Organisation Legislature',
            slug='test-org-legislature',
            kind=orgkind_legislature,
        )

        self.org_other = models.Organisation.objects.create(
            name='Test Organisation Other',
            slug='test-org-other',
            kind=orgkind,
        )

        # Create position titles

        self.positiontitle_member = models.PositionTitle.objects.create(
            name='Member',
            slug='member',
        )

        self.positiontitle_delegate = models.PositionTitle.objects.create(
            name='Delegate',
            slug='delegate',
        )

        self.positiontitle_other = models.PositionTitle.objects.create(
            name='Other',
            slug='other',
        )

    def test_related_positions(self):

        # Related by Assembly, should be counted

        person_related_assembly = models.Person.objects.create(
            name='Test Person Related Assembly',
            slug='test-person-related-assembly',
        )

        models.Position.objects.create(
            organisation=self.org_assembly,
            place=self.place,
            title=self.positiontitle_member,
            person=person_related_assembly,
            category='political',
            end_date='future',
        )

        # Related by NCOP, should be counted

        person_related_ncop = models.Person.objects.create(
            name='Test Person Related NCOP',
            slug='test-person-related-ncop',
        )

        models.Position.objects.create(
            organisation=self.org_ncop,
            place=self.place,
            title=self.positiontitle_delegate,
            person=person_related_ncop,
            category='political',
            end_date='future',
        )

        # Related by Legislature, should be counted

        person_related_legislature = models.Person.objects.create(
            name='Test Person Related Legislature',
            slug='test-person-related-legislature',
        )

        models.Position.objects.create(
            organisation=self.org_legislature,
            place=self.place,
            title=self.positiontitle_member,
            person=person_related_legislature,
            category='political',
            end_date='future',
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(1, resp.context['national_assembly_people_count'])
        self.assertEqual(1, resp.context['ncop_people_count'])
        self.assertEqual(1, resp.context['legislature_people_count'])

        self.assertEqual(3, len(resp.context['related_people']))

    def test_multiple_positions(self):

        # Related by Assembly and NCOP, should be counted once

        person_related_assembly_ncop = models.Person.objects.create(
            name='Test Person Related Assembly and NCOP',
            slug='test-person-related-assembly-ncop',
        )

        models.Position.objects.create(
            organisation=self.org_assembly,
            place=self.place,
            title=self.positiontitle_member,
            person=person_related_assembly_ncop,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        models.Position.objects.create(
            organisation=self.org_ncop,
            place=self.place,
            title=self.positiontitle_delegate,
            person=person_related_assembly_ncop,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(1, resp.context['national_assembly_people_count'])
        self.assertEqual(1, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        self.assertEqual(1, len(resp.context['related_people']))

    def test_ncop_delegate(self):

        # Related by Assembly and NCOP, should be counted once

        person_related_assembly_ncop = models.Person.objects.create(
            name='Test Person Related Assembly and NCOP',
            slug='test-person-related-assembly-ncop',
        )

        models.Position.objects.create(
            organisation=self.org_ncop,
            place=self.place,
            title=self.positiontitle_delegate,
            person=person_related_assembly_ncop,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(0, resp.context['legislature_people_count'])
        self.assertEqual(1, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        self.assertEqual(1, len(resp.context['related_people']))

    def test_former_positions(self):

        # Related by Assembly, but former member, should not be counted

        person_related_assembly_former = models.Person.objects.create(
            name='Test Person Related Former Assembly',
            slug='test-person-related-assembly-former',
        )

        models.Position.objects.create(
            organisation=self.org_assembly,
            place=self.place,
            title=self.positiontitle_member,
            person=person_related_assembly_former,
            category='political',
            end_date=ApproximateDate(2000, 1, 1),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(0, resp.context['national_assembly_people_count'])
        self.assertEqual(0, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        self.assertEqual(0, len(resp.context['related_people']))

    def test_unrelated_positions(self):

        # Unrelated, should never be counted.

        person_unrelated = models.Person.objects.create(
            name='Test Person Unrelated',
            slug='test-person-unrelated',
        )

        models.Position.objects.create(
            organisation=self.org_assembly,
            title=self.positiontitle_member,
            person=person_unrelated,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(0, resp.context['national_assembly_people_count'])
        self.assertEqual(0, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        self.assertEqual(0, len(resp.context['related_people']))

    def test_other_title_positions(self):

        # Related by Other, should not be counted

        person_related_other = models.Person.objects.create(
            name='Test Person Related Other',
            slug='test-person-related-other',
        )

        models.Position.objects.create(
            organisation=self.org_other,
            place=self.place,
            title=self.positiontitle_member,
            person=person_related_other,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(0, resp.context['national_assembly_people_count'])
        self.assertEqual(0, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        # It is included in the related_people count, however, since
        # that doesn't care about which organisation the people are
        # related by.
        self.assertEqual(1, len(resp.context['related_people']))

    def test_not_member_positions(self):

        # Related by Assembly, but not a Member, should not be counted

        person_related_assembly_not_member = models.Person.objects.create(
            name='Test Person Related Assembly (Not Member)',
            slug='test-person-related-assembly-not-member',
        )

        models.Position.objects.create(
            organisation=self.org_assembly,
            place=self.place,
            title=self.positiontitle_other,
            person=person_related_assembly_not_member,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(0, resp.context['national_assembly_people_count'])
        self.assertEqual(0, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        # It is included in the related_people count, however, since
        # that doesn't care about which organisation the people are
        # related by.
        self.assertEqual(1, len(resp.context['related_people']))


@attr(country='south_africa')
class SAMembersInterestsBrowserTest(TestCase):
    def setUp(self):
        person1 = models.Person.objects.create(
            legal_name='Alice Smith',
            slug='asmith')

        person2 = models.Person.objects.create(
            legal_name='Bob Smith',
            slug='bobsmith'
        )

        org_kind_party, created = models.OrganisationKind.objects.get_or_create(
            name='Party',
            slug='party')

        org_kind_committee, created = models.OrganisationKind.objects.get_or_create(
            name='Committee',
            slug='committee')

        party1, created = models.Organisation.objects.get_or_create(
            name='Party1',
            kind=org_kind_party,
            slug='party1')
        party2, created = models.Organisation.objects.get_or_create(
            name='Party2',
            kind=org_kind_party,
            slug='party2')

        models.Position.objects.create(person=person1, organisation=party1)
        models.Position.objects.create(person=person2, organisation=party1)

        category1 = Category.objects.create(name=u"Category A", sort_order=1)
        category2 = Category.objects.create(name=u"Category B", sort_order=2)
        category3 = Category.objects.create(name=u"Sponsorships", sort_order=3)

        release1 = Release.objects.create(
            name=u'2013 Data',
            date=date(2013, 2, 16))
        release2 = Release.objects.create(
            name=u'2012 Data',
            date=date(2012, 2, 24))

        entry1 = Entry.objects.create(
            person=person1,
            release=release1,
            category=category1,
            sort_order=1)
        entry2 = Entry.objects.create(
            person=person1,
            release=release1,
            category=category1,
            sort_order=2)
        entry3 = Entry.objects.create(
            person=person1,
            release=release1,
            category=category2,
            sort_order=3)
        entry4 = Entry.objects.create(
            person=person1,
            release=release2,
            category=category2,
            sort_order=3)
        entry5 = Entry.objects.create(
            person=person2,
            release=release1,
            category=category1,
            sort_order=4)

        EntryLineItem.objects.create(entry=entry1,key=u'Field1',value=u'Value1')
        EntryLineItem.objects.create(entry=entry1,key=u'Source',value=u'Source1')
        EntryLineItem.objects.create(entry=entry2,key=u'Field1',value=u'Value3')
        EntryLineItem.objects.create(entry=entry2,key=u'Source',value=u'Source1')
        EntryLineItem.objects.create(entry=entry3,key=u'Source',value=u'Source2')
        EntryLineItem.objects.create(entry=entry4,key=u'Source',value=u'Source2')

    def test_members_interests_browser_complete_view(self):
        context = self.client.get(reverse('sa-interests-index')).context

        #one section for each year of declarations
        self.assertEqual(len(context['data']), 2)
        self.assertTrue('person' in context['data'][0])
        self.assertTrue('data' in context['data'][0])
        self.assertTrue('year' in context['data'][0])
        self.assertTrue('category' in context['data'][0]['data'][0])
        self.assertTrue('data' in context['data'][0]['data'][0])
        self.assertTrue('headers' in context['data'][0]['data'][0])
        self.assertEqual(
            len(context['data'][0]['data'][0]['data'][len(context['data'][0]['data'][0]['data'])-1]),
            len(context['data'][0]['data'][0]['headers']))

        #test year filter
        context = self.client.get(reverse('sa-interests-index')+'?release=2013-data').context
        self.assertEqual(len(context['data']), 2)

        #test party filter
        context = self.client.get(
            reverse('sa-interests-index')+'?party=party1'
        ).context
        self.assertEqual(len(context['data']), 2)
        context = self.client.get(reverse('sa-interests-index')+'?party=party2').context
        self.assertEqual(len(context['data']), 0)

    def test_members_interests_browser_section_view(self):
        context = self.client.get(reverse('sa-interests-index')+'?category=category-a').context
        self.assertEqual(len(context['data']), 3)
        self.assertTrue('headers' in context)
        self.assertEqual(len(context['data'][0]), len(context['headers']))

        #party filter
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-a&party=party1'
        ).context
        self.assertEqual(len(context['data']), 3)
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-a&party=party2'
        ).context
        self.assertEqual(len(context['data']), 0)

        #release filter
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-b&release=2012-data'
        ).context
        self.assertEqual(len(context['data']), 1)

    def test_members_interests_browser_numberbyrepresentative_view(self):
        context = self.client.get(
            reverse('sa-interests-index')+'?display=numberbyrepresentative'
        ).context
        self.assertEqual(len(context['data']), 3)
        self.assertEqual(context['data'][0].c, 2)

        #release filter
        context = self.client.get(
            reverse('sa-interests-index')+'?display=numberbyrepresentative&release=2013-data'
        ).context
        self.assertEqual(len(context['data']), 3)
        self.assertEqual(context['data'][0].c, 2)

    def test_members_interests_browser_numberbysource_view(self):
        context = self.client.get(
            reverse('sa-interests-index')+'?display=numberbysource'
        ).context
        self.assertEqual(len(context['data']), 2)
        self.assertEqual(context['data'][0].c, 2)

        #release filter
        context = self.client.get(
            reverse('sa-interests-index')+'?display=numberbyrepresentative&release=2012-data'
        ).context
        self.assertEqual(len(context['data']), 1)
        self.assertEqual(context['data'][0].c, 1)

    def test_members_interests_browser_sources_view(self):
        context = self.client.get(
            reverse('sa-interests-source')+'?release=all&category=category-a&match=absolute&source=Source1'
        ).context
        self.assertEqual(len(context['data']), 2)

        #release filter
        context = self.client.get(
            reverse('sa-interests-source')+'?release=2012-data&category=category-b&match=absolute&source=Source2'
        ).context
        self.assertEqual(len(context['data']), 1)

        #contains filter
        context = self.client.get(
            reverse('sa-interests-source')+'?release=all&category=category-a&match=contains&source=Source'
        ).context
        self.assertEqual(len(context['data']), 2)


@attr(country='south_africa')
class SACommentsArchiveTest(WebTest):
    def setUp(self):
        blog_page1 = InfoPage.objects.create(
            title='1',
            slug='no-comments',
            markdown_content="blah",
            kind=InfoPage.KIND_BLOG
        )

        blog_page2 = InfoPage.objects.create(
            title='2',
            slug='infographic-decline-sa-tourism-2015',
            markdown_content="blah",
            kind=InfoPage.KIND_BLOG,
            )

        org_kind_constituency, _ = models.OrganisationKind.objects.get_or_create(
            name='Constituency',
            slug='constituency',
            )

        org_kind_office, _ = models.OrganisationKind.objects.get_or_create(
            name='Office',
            slug='office',
            )

        models.Organisation.objects.get_or_create(
            name='Western Cape',
            kind=org_kind_constituency,
            slug='cope-constituency-office-western-cape',
            )

        models.Organisation.objects.get_or_create(
            name='ANC Office 748',
            kind=org_kind_office,
            slug='anc-constituency-office-748-cleary-park',
            )

    @override_settings(FACEBOOK_APP_ID='test')
    def test_matching_page(self):
        path = '/blog/infographic-decline-sa-tourism-2015'
        context = self.app.get(path).context
        self.assertEqual(context['archive_link'], 'http://www.pa.org.za' + path)

    @override_settings(FACEBOOK_APP_ID='test')
    def test_matching_page_with_trailing_slash(self):
        path = "/organisation/anc-constituency-office-748-cleary-park/"
        context = self.app.get(path).context
        self.assertEqual(context['archive_link'], 'http://www.pa.org.za' + path)

    @override_settings(FACEBOOK_APP_ID='test')
    def test_matching_page_with_query(self):
        """Check Disqus comments include the query string.

        This is actually undesirable, but we may as well at least record
        the current behaviour. If we can find a way to move this comment
        to '/organisation/cope-constituency-office-western-cape',
        then this test should be updated to point to the better location.
        """
        path = '/organisation/cope-constituency-office-western-cape/?gclid=Cj0KEQjwl6GuBRD8x4G646HX7ZYBEiQADGnzujwPuJDcqQKiAI5i8mGSUCYEnxvemFlWTtPeVTMGy0waAnAw8P8HAQ'
        context = self.app.get(path).context
        self.assertEqual(context['archive_link'], 'http://www.pa.org.za' + path)

    @override_settings(FACEBOOK_APP_ID='test')
    def test_non_matching_page(self):
        context = self.app.get('/blog/no-comments').context
        self.assertEqual(context['archive_link'], None)

    @override_settings(FACEBOOK_APP_ID=None)
    def test_no_fb_app_id_no_archive_link(self):
        path = '/blog/infographic-decline-sa-tourism-2015'
        context = self.app.get(path).context
        self.assertFalse('archive_link' in context)


@attr(country='south_africa')
class SAUrlRoutingTest(TestCase):
    """Check South Africa doesn't override URLs with slug versions."""

    def test_person_all(self):
        match = resolve('/person/all/')
        self.assertEqual(match.url_name, 'person_list')

    def test_person_politicians(self):
        match = resolve('/person/politicians/')
        self.assertIn('function RedirectView', unicode(match.func))
        self.assertEqual(
            match.func.func_closure[1].cell_contents,
            {'url': '/position/mp', 'permanent': True},
            )

    def test_organisation_all(self):
        match = resolve('/organisation/all/')
        self.assertEqual(match.url_name, 'organisation_list')

    def test_place_all(self):
        match = resolve('/place/all/')
        self.assertEqual(match.url_name, 'place_kind_all')

    def test_za_organisation_people(self):
        match = resolve('/organisation/foo/people/')
        self.assertEqual(match.func.func_name, 'SAOrganisationDetailSubPeople')

    def test_za_organisation_people_prefix(self):
        match = resolve('/organisation/foo/people/A')
        self.assertEqual(match.func.func_name, 'SAOrganisationDetailSubPeople')

    def test_za_organisation(self):
        match = resolve('/organisation/foo/')
        self.assertEqual(match.func.func_name, 'SAOrganisationDetailView')

    def test_za_organisation_party(self):
        match = resolve('/organisation/foo/party/bar/')
        self.assertEqual(match.func.func_name, 'SAOrganisationDetailSubParty')

    def test_za_person(self):
        match = resolve('/person/foo/')
        self.assertEqual(match.func.func_name, 'SAPersonDetail')

    def test_za_person_appearances(self):
        match = resolve('/person/foo/appearances/')
        self.assertEqual(match.url_name, 'sa-person-appearances')
        self.assertEqual(match.func.func_name, 'RedirectView')

        self.assertEqual(
            match.func.func_closure[1].cell_contents,
            {'pattern_name': 'person', 'permanent': False},
            )

    def test_za_person_appearance(self):
        match = resolve('/person/foo/appearances/bar')
        self.assertEqual(match.func.func_name, 'SAPersonAppearanceView')

    def test_za_place(self):
        match = resolve('/place/foo/')
        self.assertEqual(match.func.func_name, 'SAPlaceDetailView')

    def test_za_place_places(self):
        match = resolve('/place/foo/places/')
        self.assertEqual(match.func.func_name, 'SAPlaceDetailSub')

    def test_za_latlon(self):
        match = resolve('/place/latlon/1.2,3.4/')
        self.assertEqual(match.func.func_name, 'LatLonDetailLocalView')

    def test_za_home(self):
        match = resolve('/')
        self.assertEqual(match.func.func_name, 'SAHomeView')


@attr(country='south_africa')
class SAMPProfilesMainHeader(WebTest):
    def setUp(self):
        self.title1 = models.PositionTitle.objects.create(
            name='Member',
            slug='member',
        )
        self.organisation_kind1 = models.OrganisationKind.objects.create(
            name='Parliament',
            slug='parliament',
        )
        self.title2 = models.PositionTitle.objects.create(
            name='Foo',
            slug='foo',
        )
        self.organisation_kind2 = models.OrganisationKind.objects.create(
            name='Bar',
            slug='bar',
        )

    def test_mp_profiles_page_has_no_any_in_the_header(self):
        response = self.app.get('/position/member/parliament/')
        self.assertEqual(
            response.html.find(class_='page-title').string, 'Members of Parliament')

    def test_pages_with_other_ok_slug_have_any_in_the_header(self):
        response = self.app.get('/position/member/bar/')
        self.assertEqual(
            response.html.find(class_='page-title').string, 'Member of any Bar')

    def test_pages_with_other_position_title_have_any_in_the_header(self):
        response = self.app.get('/position/foo/parliament/')
        self.assertEqual(
            response.html.find(class_='page-title').string, 'Foo of any Parliament')


@attr(country='south_africa')
class SAMPProfilesSubHeader(WebTest):
    def setUp(self):
        self.title1 = models.PositionTitle.objects.create(
            name='Member',
            slug='member',
        )
        self.organisation_kind1 = models.OrganisationKind.objects.create(
            name='Parliament',
            slug='parliament',
        )
        self.title2 = models.PositionTitle.objects.create(
            name='Foo',
            slug='foo',
        )
        self.organisation_kind2 = models.OrganisationKind.objects.create(
            name='Bar',
            slug='bar',
        )

    def test_mp_profiles_page_has_no_subheader(self):
        response = self.app.get('/position/member/parliament/')
        self.assertTrue(
            response.html.find(class_='content_box').find('h3') is None)

    def test_pages_with_other_ok_slug_have_the_subheader(self):
        response = self.app.get('/position/member/bar/')
        self.assertEqual(
            response.html.find(class_='content_box').find('h3').string,
            'Current Position Holders')

    def test_pages_with_other_position_title_have_the_subheader(self):
        response = self.app.get('/position/foo/parliament/')
        self.assertEqual(
            response.html.find(class_='content_box').find('h3').string,
            'Current Position Holders')


@attr(country='south_africa')
class SACommitteesPopoloJSONTest(TestCase):
    def setUp(self):
        self.email_kind = models.ContactKind.objects.create(name='Email', slug='email')

    def test_produces_correct_json_with_no_contacts(self):
        response = self.client.get('/api/committees/popolo.json')
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, {'persons': []})

    def test_produces_correct_json_with_contacts(self):
        org_kind_na_committee = models.OrganisationKind.objects.create(
            name='National Assembly Committees',
            slug='national-assembly-committees'
        )
        org = models.Organisation.objects.create(
            slug='committee-communications',
            name='PC on Communications',
            kind=org_kind_na_committee
        )
        org.contacts.create(kind=self.email_kind, value='test@example.org', preferred=False)

        response = self.client.get('/api/committees/popolo.json')
        self.assertEquals(response.status_code, 200)

        expected_json = {
            'persons': [
                {
                    'contact_details': [],
                    'email': 'test@example.org',
                    'id': str(org.id),
                    'name': 'PC on Communications'
                }
            ]
        }
        self.assertJSONEqual(response.content, expected_json)
