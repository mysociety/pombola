# -*- coding: utf-8 -*-

from __future__ import print_function

from StringIO import StringIO
import csv
from pprint import pprint
import re
from tempfile import NamedTemporaryFile

import requests

from django.core.management.base import BaseCommand, CommandError

from mapit.models import Area, Generation


office_data_url = 'https://docs.google.com/a/mysociety.org/spreadsheets/d/1bjYtGjCVill5mQPeqVgYF6nHAsyGcEnR0ZmfTXqlhjE/export?format=csv&gid=0'


cons_name_fixes = {
    'North Imenti,Meru': 'North Imenti',
    'Imenti Central': 'CENTRAL IMENTI',
    'Imenti South': 'SOUTH IMENTI',
    'Chuka/ Igamban’gombe': "CHUKA/IGAMBANG'OMBE",
}


def get_most_overlapping_area(smaller_area, larger_area_type, generation):
    intersections = []
    for area in Area.objects.intersect(
        'intersects', smaller_area, [larger_area_type], generation
    ):
        # Now work out the % intersection between the two:
        self_geos_geometry = smaller_area.polygons.collect()
        if self_geos_geometry.area == 0:
            continue
        other_geos_geometry = area.polygons.collect()
        intersection = self_geos_geometry.intersection(other_geos_geometry)
        proportion_shared = intersection.area / self_geos_geometry.area
        intersections.append((proportion_shared, area))
    if not intersections:
        return None
    if len(intersections) == 1:
        result = intersections
    result = max(intersections, key=lambda x: x[0])
    return result[1]


def dump_office_data(augmented_rows, output_filename):
    # Now prepare the data to dump:
    data_to_dump = [
        {
            'cons_name': row['MapIt Constituency'].name,
            'cons_id': row['MapIt Constituency'].id,
            'prov_name': row['MapIt Province'].name,
            'prov_id': row['MapIt Province'].id,
            'coun_name': row['MapIt County'].name,
            'coun_id': row['MapIt County'].id,
            'address': row.get('Address', ''),
            'telephone': row.get('Telephone', ''),
            'missing': 'Address' not in row,
        }
        for row in augmented_rows
    ]
    with open(output_filename, 'w') as f:
        f.write('''# This was generated from ./manage.py kenya_import_electoral_offices

IEBC_OFFICE_DATA = ''')
        pprint(data_to_dump, f)
    print("Data was dumped to:", output_filename)


class Command(BaseCommand):
    help = 'Parse data about the location of electoral offices'

    def add_arguments(self, parser):
        parser.add_argument(
            'OUTPUT-FILENAME',
            help='The filename where office data will be output (as Python)',
        )

    def handle(*args, **options):
        generation = Generation.objects.current()
        r = requests.get(office_data_url)
        reader = csv.DictReader(StringIO(r.content))
        constituencies_seen = set()
        augmented_rows = []
        for row in reader:
            region = row['Region']
            cons = re.sub(r'\s+', ' ', row['Constituency'].strip())
            cons = cons_name_fixes.get(cons, cons)
            # There seem to be some regional offices in here, which
            # aren't constituencies, AFAICT:
            if cons in ('REGION OFFICE', 'Regional Office'):
                continue
            mapit_cons = Area.objects.get(
                name__iexact=cons,
                type__code='CON',
                generation_high=generation,
            )
            constituencies_seen.add(mapit_cons.id)
            print("mapit_cons:", mapit_cons, "id:", mapit_cons.id)
            covering_province = get_most_overlapping_area(
                mapit_cons, 'PRO', generation
            )
            covering_county = get_most_overlapping_area(
                mapit_cons, 'DIS', generation
            )
            print("covering province:", covering_province, "=>", region)
            row['MapIt Constituency'] = mapit_cons
            row['MapIt Province'] = covering_province
            row['MapIt County'] = covering_county
            augmented_rows.append(row)
        # Now go through each constituency in MapIt and print out any
        # that are missing so we can find out about them:
        missing = []
        for a in Area.objects.filter(
                type__code='CON',
                generation_high__gte=generation,
                generation_low__lte=generation,
        ).exclude(id__in=constituencies_seen):
            # Now try to find the enclosing province:
            covering_province = get_most_overlapping_area(a, 'PRO', generation)
            covering_county = get_most_overlapping_area(a, 'DIS', generation)
            missing.append((covering_county, a))
            augmented_rows.append({
                'MapIt Constituency': a,
                'MapIt Province': covering_province,
                'MapIt County': covering_county,
            })
        missing.sort(key=lambda t: (t[0].name, t[1].name))
        for county, cons in missing:
            print(
                "In the county:", county,
                "couldn't find the constituency:", cons,
            )
        dump_office_data(augmented_rows, options['OUTPUT-FILENAME'])
