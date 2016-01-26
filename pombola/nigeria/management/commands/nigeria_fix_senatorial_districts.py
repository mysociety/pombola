# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from collections import defaultdict
import csv
from os.path import dirname, join
import re

from mapit.models import Area, Geometry, NameType, Type

from django.contrib.gis.geos import GEOSGeometry
from django.core.management import BaseCommand
from django.db import transaction

NAMES_TO_ADD = (
    (('SEN', 'AKWA IBOM NORTH WEST'), 'Akwa Ibom North-West'),
    (('SEN', 'AKWA IBOM NORTH EAST'), 'Akwa Ibom North-East'),
    (('SEN', 'BENUE NORTH WEST'), 'Benue North-West'),
    (('SEN', 'BENUE NORTH EAST'), 'Benue North-East'),
    (('SEN', 'JIGAWA NORTH – EAST'), 'Jigawa North East'),
    (('SEN', 'JIGAWA NORTH - WEST'), 'Jigawa North West'),
    (('SEN', 'JIGAWA SOUTH – WEST'), 'Jigawa South West'),
    (('SEN', 'Katsina (K) SOUTH'), 'Katsina South'),
    (('SEN', 'Katsina (K) CENTRAL'), 'Katsina Central'),
    (('SEN', 'Katsina (K) NORTH'), 'Katsina North'),
    (('SEN', 'Nassaraw NORTH'), 'Nasarawa North'),
    (('SEN', 'Nassaraw SOUTH'), 'Nasarawa South'),
    (('SEN', 'Nassaraw WEST'), 'Nasarawa West'),
    (('SEN', 'FEDERAL CAPITAL TERRITORY'), 'FCT Senate'),
    (('LGA', 'Nasarawa'), 'Nassarawa'),
    (('LGA', 'Nassaraw'), 'Nassarawa'),
)


class NoAreaFound(Exception):
    pass


class AmbiguousAreaName(Exception):
    pass


class Command(BaseCommand):

    def get_mapit_area(self, name, type_code, parent=None):
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)

        area_kwargs = {'name__iexact': name}
        if parent is not None:
            area_kwargs['parent_area'] = parent
        mapit_type = Type.objects.get(code=type_code)
        areas = list(mapit_type.areas.filter(**area_kwargs))
        if len(areas) > 1:
            msg = 'Ambiguous name / type: {0} ({1})'.format(name, type_code)
            raise AmbiguousAreaName(msg)
        elif len(areas) == 1:
            return areas[0]
        else:
            # No areas found; try the alternative names:
            area_kwargs = {'names__name__iexact': name}
            if parent is not None:
                area_kwargs['parent_area'] = parent
            areas = list(mapit_type.areas.filter(**area_kwargs).distinct())
            if len(areas) > 1:
                msg = 'Ambiguous alt name / type: {0} ({1})'.format(
                    name, type_code
                )
                raise AmbiguousAreaName(msg)
            elif len(areas) == 1:
                return areas[0]
            else:
                msg = 'No name / alt name found for: {0} ({1})'.format(
                    name, type_code
                )
                raise NoAreaFound(msg)

    def handle(self, *args, **options):
        with transaction.atomic():
            self.handle_inner(self, *args, **options)

    def handle_inner(self, *args, **options):

        alternative_name_type, _ = NameType.objects.get_or_create(
            code='atlas',
            defaults={'description': 'Name from the Political Atlas for SYE'},
        )
        for t, alternative_name in NAMES_TO_ADD:
            type_code, canonical_name = t
            Area.objects.get(
                name=canonical_name,
                type__code=type_code,
            ).names.get_or_create(
                type=alternative_name_type,
                name=alternative_name,
            )

        # It looks as if the original import created these senatorial
        # districts with the wrong name; they still have positions
        # associated with them, though, so just rename them:
        for old_name, new_name in (
                ('Kuje CENTRAL', 'Kogi Central'),
                ('Kuje EAST', 'Kogi East'),
                ('Kuje WEST', 'Kogi West'),
        ):
            Area.objects.filter(
                name=old_name, type__code='SEN'
            ).update(name=new_name)

        # Set the senatorial district parents of a couple of LGAs with
        # ambiguous names:
        for area_name, old_parent, new_parent in (
                ('Obi',
                 Area.objects.get(name='Benue', type__code='STA'),
                 Area.objects.get(name='BENUE SOUTH', type__code='SEN')),
                ('Obi',
                 Area.objects.get(name='Nassarawa', type__code='STA'),
                 Area.objects.get(name='Nassaraw SOUTH', type__code='SEN')),
                ('Nassaraw',
                 Area.objects.get(name='Kano', type__code='STA'),
                 Area.objects.get(name='KANO CENTRAL', type__code='SEN')),
                ('Nasarawa',
                 Area.objects.get(name='Nassarawa', type__code='STA'),
                 Area.objects.get(name='Nassaraw WEST', type__code='SEN')),
                ('Bassa',
                 Area.objects.get(name='Kogi', type__code='STA'),
                 Area.objects.get(name='Kogi East', type__code='SEN')),
                ('Bassa',
                 Area.objects.get(name='Plateau', type__code='STA'),
                 Area.objects.get(name='PLATEAU NORTH', type__code='SEN')),
                ('Ifelodun',
                 Area.objects.get(name='Kwara', type__code='STA'),
                 Area.objects.get(name='KWARA SOUTH', type__code='SEN')),
                ('Ifelodun',
                 Area.objects.get(name='Osun', type__code='STA'),
                 Area.objects.get(name='OSUN CENTRAL', type__code='SEN')),
                ('Irepodun',
                 Area.objects.get(name='Kwara', type__code='STA'),
                 Area.objects.get(name='KWARA SOUTH', type__code='SEN')),
                ('Irepodun',
                 Area.objects.get(name='Osun', type__code='STA'),
                 Area.objects.get(name='OSUN CENTRAL', type__code='SEN')),
                ('Surulere',
                 Area.objects.get(name='Oyo', type__code='STA'),
                 Area.objects.get(name='OYO CENTRAL', type__code='SEN')),
                ('Surulere',
                 Area.objects.get(name='Lagos', type__code='STA'),
                 Area.objects.get(name='LAGOS CENTRAL', type__code='SEN')),
        ):
            Area.objects.filter(
                name__iexact=area_name,
                parent_area=old_parent
            ).update(parent_area=new_parent)

        atlas_filename = join(
            dirname(__file__), '..', '..', 'data',
            'Nigeria - Political Atlas for SYE.csv'
        )

        sen_to_lga_subareas = defaultdict(set)

        unknown_federal_constituencies = set()

        with open(atlas_filename) as f:
            reader = csv.DictReader(f)
            for row in reader:
                state_name = row['STATE NAME']
                mapit_state = self.get_mapit_area(state_name, 'STA')
                # print state_name, '=>', self.get_mapit_area(state_name, 'STA')
                sen_name = row['SENATORIAL DISTRICT']
                fed_name = row['FEDERAL CONSTITUENCY']
                lga_name = row['LGA NAME']
                mapit_sen = self.get_mapit_area(sen_name, 'SEN')
                print("sen", sen_name, 'mapit', mapit_sen)
                try:
                    mapit_lga = self.get_mapit_area(lga_name, 'LGA', parent=mapit_sen)
                except NoAreaFound:
                    # It's probable that the area has the wrong parent
                    # set (e.g. the state rather than the senatorial
                    # district) so if we can find it uniquely from the
                    # name, update the parent.
                    mapit_lga = self.get_mapit_area(lga_name, 'LGA')
                    mapit_lga.parent_area = mapit_sen
                    mapit_lga.save()
                mapit_lga.parent_area = mapit_sen
                mapit_lga.save()
                mapit_sen.parent_area = mapit_state
                mapit_sen.save()
                sen_to_lga_subareas[mapit_sen].add(mapit_lga)

                try:
                    self.get_mapit_area(fed_name, 'FED')
                except NoAreaFound:
                    unknown_federal_constituencies.add((fed_name, mapit_state))

        for mapit_sen, lga_subareas in sen_to_lga_subareas.items():
            mapit_lga_ids = [a.id for a in lga_subareas]
            unioned = Geometry.objects.filter(area__id__in=mapit_lga_ids) \
                .unionagg()
            geos_geometry = GEOSGeometry(unioned).ogr
            mapit_sen.polygons.all().delete()
            if geos_geometry.geom_name == 'POLYGON':
                shapes = [geos_geometry]
            else:
                shapes = geos_geometry
            for shape in shapes:
                mapit_sen.polygons.create(polygon=shape.wkb)

        # for t in sorted(unknown_federal_constituencies):
        #     print("Unknown federal constituency:", t[0], "in state", t[1])
