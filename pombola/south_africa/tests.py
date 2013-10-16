from django.contrib.gis.geos import Polygon, Point
from django.test import TestCase
from django.core.urlresolvers import reverse

from django_webtest import WebTest

from mapit.models import Type, Area, Geometry, Generation

from pombola import settings
from pombola.core import models

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
