from django.contrib.gis.geos import Polygon

from django_webtest import WebTest

from mapit.models import Type, Area, Geometry, Generation

from pombola import settings
from pombola.core import models

class ConstituencyOfficesTestCase(WebTest):
    def setUp(self):
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
            
    def test_subplaces_page(self):
        response = self.app.get('/place/test_province/places/')

    def tearDown(self):
        settings.MAPIT_AREA_SRID = self.old_srid
