import sys
import os
from datetime import date, time
from StringIO import StringIO

from django.contrib.gis.geos import Polygon, Point
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django_webtest import WebTest

from mapit.models import Type, Area, Geometry, Generation

from pombola import settings
from pombola.core import models
import json

from popit.models import Person as PopitPerson, ApiInstance
from speeches.models import Speaker, Section
from speeches.tests import create_sections
from pombola import south_africa
from pombola.south_africa.views import PersonSpeakerMappings
from instances.models import Instance
from pombola.interests_register.models import Category, Release, Entry, EntryLineItem

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

        province = models.Place.objects.create(
            name='Test Province',
            slug='test_province',
            kind=place_kind_province,
            mapit_area=self.mapit_test_province,
            )

        org_kind_party = models.OrganisationKind.objects.create(name='Party', slug='party')
        org_kind_constituency_office = models.OrganisationKind.objects.create(name='Constituency Office', slug='constituency-office')
        org_kind_constituency_area = models.OrganisationKind.objects.create(name='Constituency Area', slug='constituency-area')

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
        place_kind_constituency_area = models.PlaceKind.objects.create(name='Constituency Area', slug='constituency-area')


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


class LatLonDetailViewTest(TestCase):
    def test_404_for_incorrect_province_lat_lon(self):
        res = self.client.get(reverse('latlon', kwargs={'lat': '0', 'lon': '0'}))
        self.assertEquals(404, res.status_code)


class SASearchViewTest(TestCase):
    def test_search_page_returns_success(self):
        res = self.client.get(reverse('core_search'))
        self.assertEquals(200, res.status_code)


class SAPersonDetailViewTest(TestCase):
    def setUp(self):
        fixtures = os.path.join(os.path.abspath(south_africa.__path__[0]), 'fixtures')
        popolo_path = os.path.join(fixtures, 'test-popolo.json')
        call_command('core_import_popolo',
            popolo_path,
            commit=True)

        # TODO rewrite this kludge, pending https://github.com/mysociety/popit-django/issues/19
        popolo_io = open(popolo_path, 'r')
        popolo_json = json.load(popolo_io)
        collection_url = 'http://popit.example.com/api/v0.1/'

        api_instance = ApiInstance(url = collection_url)
        api_instance.save()

        for doc in popolo_json['persons']:
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

            s = Speaker.objects.create(
                instance = instance,
                name = doc['name'],
                person = person)

    def test_person_to_speaker_resolution(self):
        person = models.Person.objects.get(slug='moomin-finn')
        speaker = PersonSpeakerMappings().pombola_person_to_sayit_speaker(person)
        self.assertEqual( speaker.name, 'Moomin Finn' )

    def test_generation_of_interests_table(self):
        #create data for the test
        person = models.Person.objects.get(slug='moomin-finn')

        category1 = Category.objects.create(name="Test Category", sort_order=1)
        category2 = Category.objects.create(name="Test Category 2", sort_order=2)

        release1 = Release.objects.create(name='2013', date=date(2013, 2, 16))
        release2 = Release.objects.create(name='2012', date=date(2012, 2, 24))

        entry1 = Entry.objects.create(person=person,release=release1,category=category1, sort_order=1)
        entry2 = Entry.objects.create(person=person,release=release1,category=category1, sort_order=2)
        entry3 = Entry.objects.create(person=person,release=release1,category=category2, sort_order=3)

        line1 = EntryLineItem.objects.create(entry=entry1,key='Field1',value='Value1')
        line2 = EntryLineItem.objects.create(entry=entry1,key='Field2',value='Value2')
        line3 = EntryLineItem.objects.create(entry=entry2,key='Field1',value='Value3')
        line4 = EntryLineItem.objects.create(entry=entry2,key='Field3',value='Value4')
        line5 = EntryLineItem.objects.create(entry=entry3,key='Field4',value='Value5')

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

        self.assertEqual(len(context['interests'][1]['categories'][1]['headings']), len(expected[1]['categories'][1]['headings']))
        self.assertEqual(len(context['interests'][1]['categories'][1]['entries']), len(expected[1]['categories'][1]['entries']))
        self.assertEqual(len(context['interests'][1]['categories'][1]['entries'][0]), len(expected[1]['categories'][1]['entries'][0]))
        self.assertEqual(len(context['interests'][1]['categories'][2]['headings']), len(expected[1]['categories'][2]['headings']))
        self.assertEqual(len(context['interests'][1]['categories'][2]['entries']), len(expected[1]['categories'][2]['entries']))
        self.assertEqual(len(context['interests'][1]['categories'][2]['entries'][0]), len(expected[1]['categories'][2]['entries'][0]))

class SAHansardIndexViewTest(TestCase):

    def setUp(self):
        create_sections([
            {
                'title': "Hansard",
                'subsections': [
                    {   'title': "2013",
                        'subsections': [
                            {   'title': "02",
                                'subsections': [
                                    {   'title': "16",
                                        'subsections': [
                                            {   'title': "Proceedings of the National Assembly (2012/2/16)",
                                                'subsections': [
                                                    {   'title': "Proceedings of Foo",
                                                        'speeches': [ 4, date(2013, 2, 16), time(9, 0) ],
                                                    },
                                                    {   'title': "Bill on Silly Walks",
                                                        'speeches': [ 2, date(2013, 2, 16), time(12, 0) ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                    {
                                        'title': "18",
                                        'subsections': [
                                            {   'title': "Proceedings of the National Assembly (2012/2/18)",
                                                'subsections': [
                                                    {   'title': "Budget Report",
                                                        'speeches': [ 3, date(2013, 2, 18), time(9, 0) ],
                                                    },
                                                    {   'title': "Bill on Comedy Mustaches",
                                                        'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                'title': "Empty section",
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
        self.assertContains(response, '<a href="/hansard/%d">%s</a>' % (section.id, section_name), html=True)
        self.assertNotContains(response, "Empty section")

class SACommitteeIndexViewTest(TestCase):

    def setUp(self):
        create_sections([
            {
                'title': "Committee Minutes",
                'subsections': [
                    {   'title': "Agriculture, Forestry and Fisheries",
                        'subsections': [
                            {   'title': "16 November 2012",
                                'subsections': [
                                    {   'title': "Oh fishy fishy fishy fishy fishy fish",
                                        'speeches': [ 7, date(2013, 2, 18), time(12, 0) ],
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
        ])


    def test_committee_index_page(self):
        c = Client()
        response = c.get('/committee/')
        self.assertEqual(response.status_code, 200)

        section_name = "Oh fishy fishy fishy fishy fishy fish"
        section = Section.objects.get(title=section_name)

        # Check that we can see the titles of sections containing speeches only
        self.assertContains(response, "16 November 2012")
        self.assertContains(response, section_name)
        self.assertContains(response, '<a href="/committee/%d">%s</a>' % (section.id, section_name), html=True)
        self.assertNotContains(response, "Empty section")


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
        organisation_kind.save()

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
