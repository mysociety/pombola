import sys
import os
from datetime import date, time

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
from speeches.models import Speaker
from speeches.tests import create_sections
from pombola import south_africa
from pombola.south_africa.views import SAPersonDetail
from instances.models import Instance

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
        detail = SAPersonDetail( object=person )
        speaker = detail.get_sayit_speaker()
        self.assertEqual( speaker.name, 'Moomin Finn' )


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

        # Check that we can see the titles of sections containing speeches only
        self.assertContains(response, "Proceedings of the National Assembly (2012/2/16)")
        self.assertNotContains(response, "Empty section")
