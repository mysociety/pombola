# Create boundaries in MapIt for South Africa.  You need two
# shapefiles for these, both from:
#
#   http://www.demarcation.org.za/
#
# The wards shapefile I've been using is:
#
#   http://www.demarcation.org.za/Webpage%20upload/National%20dataset%20update%20MDB%20Wards.zip
#
# ... which let us construct the Local Municipalities and Provinces
# from the ward files.  However, it doesn't include a way of creating
# the District Municipalities, so we get them from:
#
#   http://www.demarcation.org.za/Downloads/Boundary/Districts.rar
#
# There are a couple of thing that should be noted about this import
# script:
#
#   * Much of this data seems to be in MapIt Global in any case, at
#     least down the the Local Municipality level, e.g.:
#         http://global.mapit.mysociety.org/point/4326/28.983333,-30.916667.html
#     ... but it's good for us to have the Ward level data as well.
#
#   * Ideally, one would have wanted to use the generic mapit_import
#     management via call_command, to avoid duplicating much of this
#     functionality, but in order to get the metadata in other fields
#     of the shapefile and in order to build the larger areas, it was
#     necessary to be able to examine those fields programmatically.
#     However, since then I've realised that there are shapefiles at
#     each of the levels available from here:
#         http://www.demarcation.org.za/Downloads/Boundary/initial.html
#     ... so it would be worth rewriting this to just load each of
#     these shapfiles via call_command('mapit_import'), rather than
#     constructing the larger areas through aggregation.

import re
import sys

from collections import defaultdict
from optparse import make_option

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon
from django.core.management.base import NoArgsCommand, CommandError

from mapit.models import Area, Code, CodeType, Generation, Type, NameType, Country
from mapit.management.command_utils import (
    fix_invalid_geos_polygon, save_polygons
)


def get_unicode_field(field):
    result = field.value.decode('iso-8859-1')
    return re.sub('\s+', ' ', result).strip()


def union_geometries(geometry_list):
    polygons = []
    for g in geometry_list:
        g_geos = g.geos
        geom_type = g_geos.geom_type
        if geom_type == 'Polygon':
            polygons.append(g_geos)
        elif geom_type == 'MultiPolygon':
            polygons += g_geos
        else:
            raise Exception, "Unsupported geom_type (%s) for union" % (geom_type,)
    mp = MultiPolygon(polygons)
    return mp.cascaded_union


def update_or_create_area(geometry,
                          name,
                          name_type,
                          area_type,
                          code,
                          code_type,
                          country,
                          current_generation,
                          new_generation,
                          commit):
    if code:
        areas = Area.objects.filter(codes__code=code,
                                    codes__type=code_type,
                                    type=area_type).order_by('-generation_high')
    else:
        areas = Area.objects.filter(name=name,
                                    type=area_type).order_by('-generation_high')

    create_new_area = True

    if len(areas) > 0:
        area = areas[0]
        if area.generation_low.id <= new_generation.id <= area.generation_high.id:
            print "  The area already existed in the new generation, not creating"
            create_new_area = False

    if create_new_area:
        print "  Creating a new area %s of type %s" % (name,
                                                       area_type)
        area = Area(name=name,
                    type=area_type,
                    country=country,
                    generation_low=new_generation,
                    generation_high=new_generation)

    if commit:
        area.save()
        area.names.update_or_create({'type': name_type},
                                    {'name': name})
        if code:
            area.codes.update_or_create({'type': code_type},
                                     {'code': code})
        save_polygons({area.id: (area, [geometry])})


class Command(NoArgsCommand):
    """Import South African boundaries"""

    help = 'Import shapefiles with South African boundary data'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--wards',
            help="The wards shapefile (Wards_2012.shp)"),
        make_option(
            '--districts',
            help="The district municipalities shapefile (DistrictMunicipalities2011.shp)"),
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle(self, **options):

        if not (options['wards'] and options['districts']):
            raise CommandError, "You must specify both --wards and --districts"

        current_generation = Generation.objects.current()
        new_generation     = Generation.objects.new()
        if not new_generation:
            raise Exception, "There's no inactive generation for the import"

        country = Country.objects.get(code='Z')
        ward_id_code_type = CodeType.objects.get(code='wn')
        ward_area_type = Type.objects.get(code='WRD')
        name_type = NameType.objects.get(code='S')

        # ------------------------------------------------------------------------

        # Now try to load in district municipalities:

        ds = DataSource(options['districts'])
        if len(ds) != 1:
            raise Exception, "There should be exactly 1 layer in the shapefile"

        print ds[0].fields

        district_type = Type.objects.get(code='DMN')
        district_code_type = CodeType.objects.get(code='dc')
        metropolitan_type = Type.objects.get(code='MMN')

        for feat in ds[0]:
            category_to_municipality_type = {'A': metropolitan_type,
                                            'C': district_type}
            area_type = category_to_municipality_type[feat['CATEGORY'].value]
            code = feat['DISTRICT'].value

            g = feat.geom.transform(settings.MAPIT_AREA_SRID, clone=True)
            g_geos = g.geos

            full_municipality_name = feat['MAP_TITLE'].value

            m = re.search(r'(.*) (District|Metropolitan) Municipality$',
                          full_municipality_name)
            if not m:
                msg = "Couldn't parse '%s'" % (full_municipality_name,)
                raise Exception, msg

            municipality_name = m.group(1)

            update_or_create_area(g, # geometry
                                  municipality_name,
                                  name_type,
                                  area_type, # area_type
                                  code, # code
                                  district_code_type,
                                  country,
                                  current_generation,
                                  new_generation,
                                  options['commit'])

        # ------------------------------------------------------------------------
        # Now load in the wards, and construct Local Municipalities
        # and Provinces from them:

        ds = DataSource(options['wards'])

        if len(ds) != 1:
            raise Exception, "There should be exactly 1 layer in the shapefile"

        province_name_to_geometries = defaultdict(list)
        municipality_to_geometries = {'Local': defaultdict(list),
                                      'Metropolitan': defaultdict(list)}

        for feat in ds[0]:

            province_name = get_unicode_field(feat['PROVINCE'])
            full_municipality_name = get_unicode_field(feat['MUNICNAME'])
            ward_id = get_unicode_field(feat['WARD_ID'])
            ward_number = feat['WARDNO'].value
            ward_name = full_municipality_name + " " + str(ward_number)

            # Extract the municipality type from the name - it'll be
            # either "metropolitan" or "local":
            m = re.search(r'(.*) (Local|Metropolitan) Municipality$',
                          full_municipality_name)
            if not m:
                msg = "Couldn't parse '%s'" % (full_municipality_name,)
                raise Exception, msg
            municipality_name, municipality_type = m.groups()

            if municipality_type == 'Metropolitan':
                # These have already been created from the Districts
                # shapefile.
                continue

            g = feat.geom.transform(settings.MAPIT_AREA_SRID, clone=True)
            g_geos = g.geos

            # For the single invalid case (a Polygon rather than a
            # MultiPolygon) try to fix it:
            if not g_geos.valid:
                fixed_polygon = fix_invalid_geos_polygon(g_geos)
                if fixed_polygon is None:
                    msg = "Couldn't fix the invalid polygon for ward '%s'"
                    raise Exception, msg % (ward_number,)
                g = fixed_polygon.ogr

            print "creating", ward_name, "with ward_number", ward_id

            update_or_create_area(g, # geometry
                                  ward_name,
                                  name_type,
                                  ward_area_type, # area_type
                                  ward_id, # code
                                  ward_id_code_type,
                                  country,
                                  current_generation,
                                  new_generation,
                                  options['commit'])

            # Make sure to save the ward geometry, since we'll need it
            # for building the province and municipality geometries.

            province_name_to_geometries[province_name].append(g)
            municipality_to_geometries[municipality_type][municipality_name].append(g)

        province_area_type = Type.objects.get(code='PRV')

        for province_name, geometry_list in province_name_to_geometries.items():
            print "Creating Province '%s'" % (province_name,)
            unioned = union_geometries(geometry_list)

            update_or_create_area(unioned.ogr,
                                  province_name,
                                  name_type,
                                  province_area_type,
                                  None, # code
                                  None, # code_type
                                  country,
                                  current_generation,
                                  new_generation,
                                  options['commit'])

        municipality_types = {'Local': Type.objects.get(code='LMN'),
                              'Metropolitan': Type.objects.get(code='MMN')}

        for m_type in municipality_to_geometries:
            municipality_area_type = municipality_types[m_type]
            for m_name, geometry_list in municipality_to_geometries[m_type].items():
                print "Creating %s Municipality '%s'" % (m_type, m_name)
                unioned = union_geometries(geometry_list)

                update_or_create_area(unioned.ogr,
                                      m_name,
                                      name_type,
                                      municipality_area_type,
                                      None, # code
                                      None, # code_type
                                      country,
                                      current_generation,
                                      new_generation,
                                      options['commit'])
