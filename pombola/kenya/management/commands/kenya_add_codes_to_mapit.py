from __future__ import print_function, unicode_literals

import csv
import re

from django.core.management.base import BaseCommand
from django.db import transaction
from mapit.models import Area, CodeType, Generation, NameType
import requests


URLS_WITH_COUNTY = (
    # The '2017 Kenyan County Assembly Ward Candidates' spreadsheet:
    'https://docs.google.com/a/mysociety.org/spreadsheets/d/1ZWRN6XeN6dVhWqvdikDDeMp6aFM3zJVv9cmf80NZebY/export?format=csv',
    # The '2017 Kenya Senatorial Candidates' spreadsheet:
    'https://docs.google.com/a/mysociety.org/spreadsheets/d/1x3_otOE376QFwfGO9vMC5qZxeIvGR3MR_UeflgLVLj8/export?format=csv',
    # The '2017 Kenyan County Governor Candidates' spreadsheet:
    'https://docs.google.com/a/mysociety.org/spreadsheets/d/1RxXOwbHly8nv5-wVwnRSvNx5zYEs1Xvl0bPF1hfn_NI/export?format=csv',
    # The '2017 Kenyan Women Representative Candidates' spreadsheet:
    'https://docs.google.com/a/mysociety.org/spreadsheets/d/1SPkbrnUbstmHWeIU0W3yxvOehhnj7GLHzcwWp2pGeXc/export?format=csv',
)

URLS_WITH_CONSTITUENCY = (
    # The '2017 Kenyan National Assembly Candidates' spreadsheet:
    'https://docs.google.com/a/mysociety.org/spreadsheets/d/1Ccj-yg_B92j5H9mUUCo6vaw1Zgjra0KoX9s5fzMDzJA/export?format=csv',
)


def normalize(s):
    s = re.sub(r'[-/]', ' ', s.lower())
    return re.sub(r'(?ms)\s+', ' ', s).strip()


class Command(BaseCommand):
    help = 'Add the IEBC codes to counties and constituencies in MapIt'

    @transaction.atomic
    def handle(self, **options):
        generation = Generation.objects.current()
        county_code_type, _ = CodeType.objects.get_or_create(
            code='2017_coun',
            defaults={
                'description': 'County code from the 2017 IEBC candidate data'})
        constituency_code_type, _ = CodeType.objects.get_or_create(
            code='2017_cons',
            defaults={
                'description': 'Constituency code from the 2017 IEBC candidate data'})
        name_type, _ = NameType.objects.get_or_create(
            code='iebc_2017',
            defaults={
                'description': 'Name used in the 2017 IEBC candidate data'
            }
        )
        for mapit_area_type, urls, name_heading, code_heading, code_type in (
                ('DIS', URLS_WITH_COUNTY,
                 'County Name', 'County Code', county_code_type),
                ('CON', URLS_WITH_CONSTITUENCY,
                 'Constituency Name', 'Constituency Code', constituency_code_type),
        ):
            # First get all names / codes from the spreadsheets:
            name_to_code = {}
            name_to_original_name = {}
            for url in urls:
                r = requests.get(url)
                r.raise_for_status()
                reader = csv.DictReader(r.iter_lines())
                for row in reader:
                    original_name = row[name_heading]
                    name = normalize(original_name)
                    name_to_original_name[name] = original_name
                    code = row[code_heading]
                    if name in name_to_code:
                        assert code == name_to_code[name]
                    else:
                        name_to_code[name] = code
            # Now go through all the areas in MapIt in the latest generation:
            for area in Area.objects.filter(
                    type__code=mapit_area_type,
                    generation_low__id__lte=generation.id,
                    generation_high__id__gte=generation.id):
                area_name = normalize(area.name)
                area_name = {
                    'nairobi': 'nairobi city',
                    # Suba north used to be Mbita, and Suba South used
                    # to be Suba, according to:
                    # http://www.nation.co.ke/election2017/agenda/Mbadi-is-scaling-a-tight-rope-in-third-re-election-bid-Suba/3797778-3882834-11b98g2/index.html
                    # https://thegovernorblog.wordpress.com/2016/03/20/we-are-not-suba-mbita-residents-oppose-the-change-of-constituency-name-to-suba-north/
                    'suba': 'suba south',
                    'mbita': 'suba north',
                    'lunga lunga': 'lungalunga',
                }.get(area_name, area_name)
                code = name_to_code[area_name]
                iebc_name = name_to_original_name[area_name]
                # And make sure new Code and Name objects are
                # associated with that area:
                area.codes.get_or_create(type=code_type, code=code)
                area.names.get_or_create(type=name_type, name=iebc_name)
