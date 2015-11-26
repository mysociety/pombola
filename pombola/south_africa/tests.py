from __future__ import division

import re
import os
from datetime import date, time
from StringIO import StringIO
from tempfile import mkdtemp
from urlparse import urlparse
from BeautifulSoup import Tag, NavigableString

from mock import patch

from django.contrib.gis.geos import Polygon, Point
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

# NOTE - from Django 1.7 this should be replaced with 
# django.core.cache.caches
# https://docs.djangoproject.com/en/1.8/topics/cache/#django.core.cache.caches
from django.core.cache import get_cache

from django.core.urlresolvers import reverse, resolve
from django.core.management import call_command
from django_date_extensions.fields import ApproximateDate
from django_webtest import TransactionWebTest

from mapit.models import Type, Area, Geometry, Generation

from django.conf import settings
from pombola.core import models
import json

from popit.models import Person as PopitPerson, ApiInstance
from speeches.models import Speaker, Section, Speech
from speeches.tests import create_sections
from pombola import south_africa
from pombola.south_africa.views import SAPersonDetail
from pombola.core.views import PersonSpeakerMappingsMixin
from pombola.info.models import InfoPage
from instances.models import Instance
from pombola.interests_register.models import Category, Release, Entry, EntryLineItem

from nose.plugins.attrib import attr

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
    else:
        raise Exception, u"Unexpected input to fake_geocoder: {}".format(q)

@attr(country='south_africa')
class HomeViewTest(TestCase):

    def test_homepage_context(self):
        response = self.client.get('/')
        self.assertIn('mp_corner', response.context)
        self.assertIn('news_articles', response.context)

@attr(country='south_africa')
class ConstituencyOfficesTestCase(TransactionWebTest):
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
class SASearchViewTest(TransactionWebTest):

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


@attr(country='south_africa')
class SAPersonDetailViewTest(PersonSpeakerMappingsMixin, TestCase):
    def setUp(self):
        fixtures = os.path.join(os.path.abspath(south_africa.__path__[0]), 'fixtures')
        popolo_path = os.path.join(fixtures, 'test-popolo.json')
        call_command('core_import_popolo',
            popolo_path,
            commit=True)

        # Make new Popolo JSON from the people in the database. (We now
        # assume that our PopIt instances are exported from Pombola, so we
        # need to do this step to generate Popolo JSON with IDs that are
        # based on the primary keys in the Pombola database.)

        popolo_directory = mkdtemp()
        call_command(
            'core_export_to_popolo_json',
            popolo_directory,
            'http://www.pa.org.za/'
        )

        # TODO rewrite this kludge, pending https://github.com/mysociety/popit-django/issues/19
        with open(os.path.join(popolo_directory, 'persons.json')) as f:
            popolo_person_json = json.load(f)

        collection_url = 'http://popit.example.com/api/v0.1/'

        api_instance = ApiInstance(url = collection_url)
        api_instance.save()

        for doc in popolo_person_json:
            # Add id and url to the doc
            doc['popit_id']  = doc['id']
            url = collection_url + doc['id']
            doc['popit_url'] = url

            person = PopitPerson.update_from_api_results(instance=api_instance, doc=doc)

            instance, _ = Instance.objects.get_or_create(
                label='default',
                defaults = {
                    'title': 'An instance'
                })

            Speaker.objects.create(
                instance = instance,
                name = doc['name'],
                person = person)

        # Create the top level SayIt sections, so that there's no
        # warning when getting the person page:
        create_sections([{'title': u"Hansard"},
                         {'title': u"Committee Minutes"},
                         {'title': u"Questions"}])

        moomin_finn = models.Person.objects.get(slug='moomin-finn')
        # Give moomin-finn a fake ID for the PMG API
        models.Identifier.objects.create(
            scheme='za.org.pmg.api/member',
            identifier=moomin_finn.slug,
            content_object=moomin_finn,
            )

        # Put blank attendance data in the cache to stop us fetching from
        # the live PMG API
        pmg_api_cache = get_cache('pmg_api')
        pmg_api_cache.set(
            "http://api.pmg.org.za/member/moomin-finn/attendance/",
            [],
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

    def test_attendance_data(self):
        test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data/test/attendance_587.json',
            )
        with open(test_data_path) as f:
            raw_data = json.load(f)

        pmg_api_cache = get_cache('pmg_api')
        pmg_api_cache.set(
            "http://api.pmg.org.za/member/moomin-finn/attendance/",
            raw_data['results'],
            )

        context = self.client.get(reverse('person', args=('moomin-finn',))).context

        self.assertEqual(
            context['attendance'],
            [{'total': 28, 'percentage': 89.28571428571429, 'attended': 25, 'year': 2015},
             {'total': 15, 'percentage': 93.33333333333333, 'attended': 14, 'year': 2014}],
            )

        self.assertEqual(
            context['latest_meetings_attended'],
            [{'url': 'https://pmg.org.za/committee-meeting/21460/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Performing Animals Protection Amendment Bill [B9-2015]: deliberations & finalisation; Plant Improvement [B8-2015] & Plant Breeders\u2019 Rights Bills [B11-2015]: Department response to Legal Advisor concerns'},
             {'url': 'https://pmg.org.za/committee-meeting/21374/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Performing Animals Protection Amendment Bill [B9-2015]: deliberations; Committee Support Officials on Plant Improvement Bill [B8-2015] and Plant Breeders\u2019 Rights Bill [B11-2015]'},
             {'url': 'https://pmg.org.za/committee-meeting/21327/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Department of Agriculture, Forestry and Fisheries 4th Quarter 2014/15 & 1st Quarter 2015/16 Performance'},
             {'url': 'https://pmg.org.za/committee-meeting/21268/',
              'committee_name': u'Agriculture, Forestry and Fisheries',
              'title': u'Performing Animals Protection Amendment Bill [B9-2015]: deliberations; Plant Improvement [B8-2015]  & Plant Breeders\u2019 Rights Bills[11-2015]: Department response to public inputs '},
             {'url': 'https://pmg.org.za/committee-meeting/21141/',
              'committee_name': u'Rural Development and Land Reform',
              'title': u'One District-One Agri-Park implementation in context of Rural Economic Transformation Model'}],
            )


@attr(country='south_africa')
class SAAttendanceDataTest(TestCase):
    def test_get_attendance_stats(self):
        raw_data = {
            2000: {'A': 1, 'AP': 2, 'DE': 4, 'L': 8, 'LDE': 16, 'P': 32},
            }

        expected = [
            {'year': 2000,
            'attended': 60,
            'total': 63,
            'percentage': 100*60/63,
             }
            ]

        stats = SAPersonDetail().get_attendance_stats(raw_data)
        self.assertEqual(stats, expected)

        raw_data = {
            2000: {'A': 1, 'P': 2},
            2001: {'A': 4, 'P': 8},
            }

        expected = [
            {'year': 2001,
             'attended': 8,
             'total': 12,
             'percentage': 100*8/12,
             },
            {'year': 2000,
             'attended': 2,
             'total': 3,
             'percentage': 100*2/3,
             }
        ]

        stats = SAPersonDetail().get_attendance_stats(raw_data)
        self.assertEqual(stats, expected)

    def test_get_attendance_stats_raw(self):
        test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data/test/attendance_587.json',
            )
        with open(test_data_path) as f:
            raw_data = json.load(f)

        raw_stats = SAPersonDetail().get_attendance_stats_raw(raw_data['results'])

        expected = {2014: {u'A': 1, u'P': 14}, 2015: {u'A': 1, u'P': 25, u'AP': 2}}

        self.assertEqual(raw_stats, expected)


@attr(country='south_africa')
class SAPersonProfileSubPageTest(TransactionWebTest):
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
        pmg_api_cache = get_cache('pmg_api')

        for person in (self.deceased, self.former_mp):
            models.Identifier.objects.create(
                scheme='za.org.pmg.api/member',
                identifier=person.slug,
                content_object=person,
                )

            pmg_api_cache.set(
                "http://api.pmg.org.za/member/{}/attendance/".format(person.slug),
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


@attr(country='south_africa')
class SAHansardIndexViewTest(TestCase):

    def setUp(self):
        create_sections([
            {
                'title': u"Hansard",
                'subsections': [
                    {   'title': u"2013",
                        'subsections': [
                            {   'title': u"02",
                                'subsections': [
                                    {   'title': u"16",
                                        'subsections': [
                                            {   'title': u"Proceedings of the National Assembly (2012/2/16)",
                                                'subsections': [
                                                    {   'title': u"Proceedings of Foo",
                                                        'speeches': [ 4, date(2013, 2, 16), time(9, 0) ],
                                                    },
                                                    {   'title': u"Bill on Silly Walks",
                                                        'speeches': [ 2, date(2013, 2, 16), time(12, 0) ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                    {
                                        'title': u"18",
                                        'subsections': [
                                            {   'title': u"Proceedings of the National Assembly (2012/2/18)",
                                                'subsections': [
                                                    {   'title': u"Budget Report",
                                                        'speeches': [ 3, date(2013, 2, 18), time(9, 0) ],
                                                    },
                                                    {   'title': u"Bill on Comedy Mustaches",
                                                        'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                'title': u"Empty section",
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
        section = Section.objects.get(title=section_name)

        # Check that we can see the titles of sections containing speeches only
        self.assertContains(response, section_name)
        self.assertContains(response, '<a href="/%s">%s</a>' % (section.get_path, section_name), html=True)
        self.assertNotContains(response, "Empty section")

@attr(country='south_africa')
class SACommitteeIndexViewTest(TransactionWebTest):

    def setUp(self):
        self.fish_section_title = u"Oh fishy fishy fishy fishy fishy fish"
        self.forest_section_title = u"Forests are totes awesome"
        self.pmq_section_title = "Questions on 20 June 2014"
        # Make sure that the default SayIt instance exists, since when
        # testing it won't be created because of SOUTH_TESTS_MIGRATE = False
        default_instance, _ = Instance.objects.get_or_create(label='default')
        create_sections([
            {
                'title': u"Committee Minutes",
                'subsections': [
                    {   'title': u"Agriculture, Forestry and Fisheries",
                        'subsections': [
                            {   'title': u"16 November 2012",
                                'subsections': [
                                    {   'title': self.fish_section_title,
                                        'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
                                    },
                                    {
                                        'title': u"Empty section",
                                    }
                                ],
                            },
                            {   'title': "17 November 2012",
                                'subsections': [
                                    {   'title': self.forest_section_title,
                                        'speeches': [ 7, date(2013, 2, 19), time(9, 0), False ],
                                    },
                                    {
                                        'title': "Empty section",
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'title': u"Hansard",
                'subsections': [
                    {   'title': u"Prime Minister's Questions",
                        'subsections': [
                            {   'title': self.pmq_section_title,
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

        section = Section.objects.get(title=self.fish_section_title)

        # Check that we can see the titles of sections containing speeches only
        self.assertContains(response, "16 November 2012")
        self.assertContains(response, self.fish_section_title)
        self.assertContains(response,
                            '<a href="/%s">%s</a>' % (section.get_path,
                                                      self.fish_section_title),
                            html=True)
        self.assertNotContains(response, "Empty section")

    def test_committee_section_redirects(self):
        # Get the section URL:
        section = Section.objects.get(title=self.fish_section_title)
        section_url = reverse('speeches:section-view', args=(section.get_path,))
        response = self.app.get(section_url)
        self.assertEqual(response.status_code, 302)
        url_match = re.search(r'http://somewhere.or.other/\d+',
                              response.location)
        self.assertTrue(url_match)

    def view_speech_in_section(self, section_title):
        section = Section.objects.get(title=section_title)
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
        self.check_redirect(self.view_speech_in_section(self.fish_section_title))

    def test_private_committee_speech_redirects(self):
        # Try a speech in a section that contains public speeches:
        self.check_redirect(self.view_speech_in_section(self.forest_section_title))

    def test_hansard_speech_returned(self):
        response = self.view_speech_in_section(self.pmq_section_title)
        self.assertEqual(response.status_code, 200)
        self.assertIn('rhubarb rhubarb', response)

@attr(country='south_africa')
class SAOrganisationDetailViewTest(TransactionWebTest):

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
class SAOrganisationDetailViewTestParliament(TransactionWebTest):

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

    def test_percentages(self):
        with self.assertNumQueries(11):
            response = self.app.get('/organisation/model-parliament/')
        ps_and_ps = response.context['parties_and_percentages']
        self.assertEqual(2, len(ps_and_ps))
        self.assertEqual(ps_and_ps[0][0], self.party_another_random)
        self.assertAlmostEqual(ps_and_ps[0][1], 66.666666666666)
        self.assertEqual(ps_and_ps[1][0], self.party_random)
        self.assertAlmostEqual(ps_and_ps[1][1], 33.333333333333)


@attr(country='south_africa')
class FixPositionTitlesCommandTests(TestCase):
    """Test the south_africa_fix_position_title command"""

    def setUp(self):
        # Create some organisations with some people in various positions,
        # with various titles
        self.person_a = models.Person.objects.create(
            name="Person A",
            slug="person-a")
        self.person_b = models.Person.objects.create(
            name="Person B",
            slug="person-b")
        self.person_c = models.Person.objects.create(
            name="Person C",
            slug="person-c")
        self.person_d = models.Person.objects.create(
            name="Person D",
            slug="person-d")

        self.party_kind = models.OrganisationKind.objects.create(
            name="Party",
            slug="party")
        self.other_kind = models.OrganisationKind.objects.create(
            name="Other Org",
            slug="other-org")

        self.organisation_a = models.Organisation.objects.create(
            name="Organisation A",
            kind=self.party_kind,
            slug="organisation-a")
        self.organisation_b = models.Organisation.objects.create(
            name="Organisation B",
            kind=self.party_kind,
            slug="organisation-b")
        self.organisation_c = models.Organisation.objects.create(
            name="Organisation C",
            kind=self.other_kind,
            slug="organisation-c")

        self.party_member_position_title = models.PositionTitle.objects.create(
            name="Party Member",
            slug="party-member")
        self.member_position_title = models.PositionTitle.objects.create(
            name="Member",
            slug="member")
        self.other_position_title = models.PositionTitle.objects.create(
            name="Other Title",
            slug="other-title")

        self.position_a = models.Position.objects.create(
            title=self.party_member_position_title,
            person=self.person_a,
            category="other",
            organisation=self.organisation_a)
        self.position_b = models.Position.objects.create(
            title=self.party_member_position_title,
            person=self.person_b,
            category="other",
            organisation=self.organisation_b)
        self.position_c = models.Position.objects.create(
            title=self.member_position_title,
            person=self.person_c,
            category="other",
            organisation=self.organisation_a)
        self.position_d = models.Position.objects.create(
            title=self.other_position_title,
            person=self.person_d,
            category="other",
            organisation=self.organisation_b)

    def test_updates_titles_and_deletes_position(self):
        self.assertEquals(
            models.Position.objects.filter(title=self.party_member_position_title).count(),
            2)
        self.assertEquals(
            models.Position.objects.filter(title=self.member_position_title).count(),
            1)

        call_command(
            'south_africa_fix_position_titles',
            stderr=StringIO(),
            stdout=StringIO())

        # Check things are re-assigned correctly
        self.assertEquals(
            models.Position.objects.filter(title=self.party_member_position_title).count(),
            0)
        self.assertEquals(
            models.Position.objects.filter(title=self.member_position_title).count(),
            3)
        self.assertEquals(
            models.Position.objects.get(id=self.position_a.id).title,
            self.member_position_title)
        self.assertEquals(
            models.Position.objects.get(id=self.position_b.id).title,
            self.member_position_title)

        # Check that the old PositionTitle is deleted
        self.assertEqual(
            models.PositionTitle.objects.filter(name="Party Member").count(),
            0)

        # Check that nothing else got clobbered
        self.assertEquals(
            models.Position.objects.get(id=self.position_c.id).title,
            self.member_position_title)
        self.assertEquals(
            models.Position.objects.get(id=self.position_d.id).title,
            self.other_position_title)


    def test_errors_if_position_titles_not_on_parties(self):
        self.person_e = models.Person.objects.create(
            name="Person E",
            slug="person-e")
        models.Position.objects.create(
            title=self.party_member_position_title,
            person=self.person_e,
            category="other",
            organisation=self.organisation_c)

        with self.assertRaises(AssertionError):
            call_command(
                'south_africa_fix_position_titles',
                stderr=StringIO(),
                stdout=StringIO())

@attr(country='south_africa')
class SAPlaceDetailViewTest(TransactionWebTest):

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
            title=self.positiontitle_member,
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
        self.assertContains(resp, "There are 3 people related to Test Place.")

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
            title=self.positiontitle_member,
            person=person_related_assembly_ncop,
            category='political',
            end_date=ApproximateDate(future=True),
        )

        resp = self.app.get('/place/test-place/')

        self.assertEqual(1, resp.context['national_assembly_people_count'])
        self.assertEqual(1, resp.context['ncop_people_count'])
        self.assertEqual(0, resp.context['legislature_people_count'])

        self.assertEqual(1, len(resp.context['related_people']))
        self.assertContains(resp, "There is 1 person related to Test Place.")

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
        person = models.Person.objects.create(
            legal_name='Alice Smith',
            slug='asmith')

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
        other_org1, created = models.Organisation.objects.get_or_create(
            name='Organisation1',
            kind=org_kind_committee,
            slug='organisation1')
        other_org2, created = models.Organisation.objects.get_or_create(
            name='Organisation2',
            kind=org_kind_committee,
            slug='organisation2')

        models.Position.objects.create(person=person, organisation=party1)
        models.Position.objects.create(person=person, organisation=other_org1)

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
            person=person,
            release=release1,
            category=category1,
            sort_order=1)
        entry2 = Entry.objects.create(
            person=person,
            release=release1,
            category=category1,
            sort_order=2)
        entry3 = Entry.objects.create(
            person=person,
            release=release1,
            category=category2,
            sort_order=3)
        entry4 = Entry.objects.create(
            person=person,
            release=release2,
            category=category2,
            sort_order=3)

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
        self.assertEqual(len(context['data']), 1)

        #test party filter
        context = self.client.get(
            reverse('sa-interests-index')+'?party=party1'
        ).context
        self.assertEqual(len(context['data']), 2)
        context = self.client.get(reverse('sa-interests-index')+'?party=party2').context
        self.assertEqual(len(context['data']), 0)

        #test membership filter
        context = self.client.get(
            reverse('sa-interests-index')+'?organisation=organisation1'
        ).context
        self.assertEqual(len(context['data']), 2)
        context = self.client.get(
            reverse('sa-interests-index')+'?organisation=organisation2'
        ).context
        self.assertEqual(len(context['data']), 0)

    def test_members_interests_browser_section_view(self):
        context = self.client.get(reverse('sa-interests-index')+'?category=category-a').context
        self.assertEqual(len(context['data']), 2)
        self.assertTrue('headers' in context)
        self.assertEqual(len(context['data'][0]), len(context['headers']))

        #party filter
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-a&party=party1'
        ).context
        self.assertEqual(len(context['data']), 2)
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-a&party=party2'
        ).context
        self.assertEqual(len(context['data']), 0)

        #organisation filter
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-a&organisation=organisation1'
        ).context
        self.assertEqual(len(context['data']), 2)
        context = self.client.get(
            reverse('sa-interests-index')+'?category=category-a&organisation=organisation2'
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
        self.assertEqual(len(context['data']), 2)
        self.assertEqual(context['data'][0].c, 2)

    def test_members_interests_browser_numberbysource_view(self):
        context = self.client.get(
            reverse('sa-interests-index')+'?display=numberbysource'
        ).context
        self.assertEqual(len(context['data']), 3)
        self.assertEqual(context['data'][0].c, 2)

        #release filter
        context = self.client.get(
            reverse('sa-interests-index')+'?display=numberbyrepresentative&release=2013-data'
        ).context
        self.assertEqual(len(context['data']), 2)
        self.assertEqual(context['data'][0].c, 2)

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
class SACommentsArchiveTest(TransactionWebTest):
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
        self.assertEqual(match.url_name, 'django.views.generic.base.RedirectView')
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

    def test_za_latlon_national(self):
        match = resolve('/place/latlon/1.2,3.4/national/')
        self.assertEqual(match.func.func_name, 'LatLonDetailNationalView')

    def test_za_latlon(self):
        match = resolve('/place/latlon/1.2,3.4/')
        self.assertEqual(match.func.func_name, 'LatLonDetailLocalView')

    def test_za_home(self):
        match = resolve('/')
        self.assertEqual(match.func.func_name, 'SAHomeView')
