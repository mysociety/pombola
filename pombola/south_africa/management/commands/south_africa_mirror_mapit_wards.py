from contextlib import closing
import os
from tempfile import NamedTemporaryFile
import time
from urlparse import urljoin

import requests

from django.contrib.gis.gdal import DataSource
from django.core.management.base import BaseCommand
from django.db import transaction

from mapit.models import Area, Country, Geometry, Generation, Type
from mapit.management.command_utils import save_polygons

SLEEP_BETWEEN_REQUESTS = 1

class Command(BaseCommand):

    def handle(self, *args, **options):
        remote_mapit_url = 'http://mapit.code4sa.org/'
        all_wards_url = urljoin(remote_mapit_url, '/areas/WD')
        r = requests.get(all_wards_url)
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        with transaction.atomic():
            # Remove existing wards from MapIt:
            Geometry.objects.filter(area__type__code='WD').delete()
            Area.objects.filter(type__code='WD').delete()
            # Get the Country object for South Africa:
            country, _ = Country.objects.get_or_create(
                name='South Africa',
                defaults={'code': 'ZA'})
            # Get the current Generation:
            generation = Generation.objects.current()
            # Make sure the ward type exists:
            ward_type, _ = Type.objects.get_or_create(
                code='WD', defaults={'description': 'Ward'})
            for wd_id, wd_data in r.json().items():
                # FIXME: we don't actually need the extra names (from
                # 'all_names'), the codes (from 'codes') or the
                # parent_area, but use the other attributes. We might
                # want to add them later.
                area = Area.objects.create(
                    country=country,
                    generation_low=generation,
                    generation_high=generation,
                    name=wd_data['name'],
                    type=ward_type,
                )
                geojson_url = urljoin(
                    remote_mapit_url,
                    '/area/{0}.geojson'.format(wd_id))
                ntf = NamedTemporaryFile(delete=False)
                print "Downloading {0} to {1}".format(geojson_url, ntf.name)
                with open(ntf.name, 'wb') as f:
                    with closing(requests.get(geojson_url)) as r:
                        f.write(r.text.encode('utf-8'))
                ds = DataSource(ntf.name)
                layer = ds[0]
                for feat in layer:
                    g = feat.geom
                    save_polygons({area.id: (area, [g])})
                os.remove(ntf.name)
                time.sleep(SLEEP_BETWEEN_REQUESTS)
