from __future__ import print_function, unicode_literals

import json
from os import listdir
from os.path import basename, isdir, join
import re

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from mapit.models import CodeType, Generation, NameType, Type

# The GeoJSON required for this script was downloaded from the IEBC API with:
#
# curl -o wards.json http://api.iebc.or.ke/ward/?token=[YOUR-TOKEN_HERE]
# for f in `jq -r .region.locations[].polygon < wards.json`; do curl -O "$f"; done


def parse_geojson(filename):
    with open(filename) as f:
        return json.load(f)


def get_properties(data):
    return data['features'][0]['properties']


def get_name_key(data):
    # Some files have the name under a different key
    properties = get_properties(data)
    for key in ('COUNTY_A_1', 'Ward_Name'):
        if key in properties:
            return key
    raise CommandError("Couldn't find a key in {0}".format(json.dumps(indent=True)))


def get_override_code(filename, data):
    properties = get_properties(data)
    if 'COUNTY_ASS' not in properties:
        # Get the ID from the filename:
        just_basename = basename(filename)
        return re.search(r'ward_(\d+)\.', just_basename).group(1)


def get_override_name(filename, data):
    properties = get_properties(data)
    name_and_code = (
        properties.get('COUNTY_A_1'),
        properties.get('COUNTY_ASS'),
    )
    if name_and_code == ('`', 1084):
        return 'LWANDANYI'
    elif name_and_code == ('673', 245):
        return 'NGARE MARA'


def has_features(data):
    return len(data['features']) > 0


class Command(BaseCommand):
    help = 'Import ward boundaries from the IEBC GeoJSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            'GENERATION-ID',
            help='The generation to import the ward boundaries into')
        parser.add_argument(
            'GEOJSON-DIRECTORY',
            help='The directory containing the ward GeoJSON files')

    @transaction.atomic
    def handle(self, **options):
        generation = Generation.objects.get(pk=options['GENERATION-ID'])
        geojson_directory = options['GEOJSON-DIRECTORY']
        if not isdir(geojson_directory):
            raise CommandError('{0} was not a directory'.format(geojson_directory))
        # Make sure the right CodeType and NameType objects exist:
        ward_code_type, _ = CodeType.objects.get_or_create(
            code='2017_ward',
            defaults={
                'description': 'Ward code from the 2017 IEBC candidate data'})
        name_type, _ = NameType.objects.get_or_create(
            code='iebc_2017',
            defaults={
                'description': 'Name used in the 2017 IEBC candidate data'
            }
        )
        area_type, _ = Type.objects.get_or_create(code='WRD', description='Ward')
        for filename in listdir(geojson_directory):
            if not filename.endswith('.geojson'):
                continue
            full_filename = join(geojson_directory, filename)
            data = parse_geojson(full_filename)
            if not has_features(data):
                msg = 'Skipping {0} because it contained not features'
                print(msg.format(full_filename))
                continue
            name_key = get_name_key(data)
            command_options = {
                'generation_id': generation.id,
                'area_type_code': 'WRD',
                'name_type_code': 'iebc_2017',
                'country_code': 'k',
                'code_type': '2017_ward',
                'commit': True,
            }
            override_code = get_override_code(full_filename, data)
            if override_code is None:
                command_options['code_field'] = 'COUNTY_ASS'
            else:
                command_options['override_code'] = override_code
            override_name = get_override_name(full_filename, data)
            if override_name is None:
                command_options['name_field'] = name_key
            else:
                command_options['override_name'] = override_name
            call_command('mapit_import', full_filename, **command_options)
