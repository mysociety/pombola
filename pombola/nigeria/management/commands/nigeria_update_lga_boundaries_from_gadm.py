from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand
from django.db import transaction

from mapit.management.command_utils import save_polygons, fix_invalid_geos_geometry
from mapit.models import Area, Type

class Command(BaseCommand):
    help = "Update the Nigeria boundaries from GADM"
    args = '<SHP FILENAME>'

    def get_lga_area(self, lga_name, state_name):
        lga_name_in_db = {
            'Eastern Obolo': 'Eastern O bolo',
        }.get(lga_name, lga_name)

        # print "state:", state_name
        kwargs = {
            'type': self.lga_type,
            'name__iexact': lga_name_in_db,
            'parent_area__name': state_name,
        }
        try:
            area = Area.objects.get(**kwargs)
        except Area.DoesNotExist:
            del kwargs['parent_area__name']
            area = Area.objects.get(**kwargs)
        return area

    def fix_geometry(self, g):
        # Make a GEOS geometry only to check for validity:
        geos_g = g.geos
        if not geos_g.valid:
            geos_g = fix_invalid_geos_geometry(geos_g)
            if geos_g is None:
                print "The geometry was invalid and couldn't be fixed"
                g = None
            else:
                g = geos_g.ogr
        return g

    def handle(self, filename, **options):
        with transaction.atomic():
            self.lga_type = Type.objects.get(code='LGA')
            ds = DataSource(filename)
            layer = ds[0]
            for feature in layer:
                lga_name = unicode(feature['NAME_2'])
                state_name = unicode(feature['NAME_1'])
                print "Updating LGA {0} in state {1}".format(
                    lga_name, state_name
                )
                area = self.get_lga_area(lga_name, state_name)
                g = feature.geom.transform('4326', clone=True)
                g = self.fix_geometry(g)
                if g is None:
                    continue
                poly = [g]
                save_polygons({area.id: (area, poly)})
