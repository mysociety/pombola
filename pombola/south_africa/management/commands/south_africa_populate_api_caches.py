import time

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

import requests

from mapit.models import Area
from pombola.core.models import Identifier, Person
from pombola.south_africa.pmg_api import (
    get_person_from_pa_url,
    update_or_create_pmg_api_identifier,
    update_attendance_data_in_cache,
    update_committee_attendance_data_in_cache,
    update_ward_councillor_data_in_cache,
)


# How long to wait between each request to an external API:
SLEEP_BETWEEN_REQUESTS = 1


class Command(BaseCommand):

    help = 'Mirror data from external APIs for better reliability'

    def handle(self, *args, **options):
        # First get the ID mapping for PMG API <-> PA, and make sure
        # that's cached.
        pmg_member_ids = set()
        page = 0
        while True:
            url = 'https://api.pmg.org.za/member/?page={0}'.format(page)
            r = requests.get(url)
            data = r.json()
            for member_data in data['results']:
                # Skip people with no PA URL:
                if not member_data.get('pa_link'):
                    continue
                person = get_person_from_pa_url(member_data['pa_link'])
                update_or_create_pmg_api_identifier(person, member_data['id'])
            if not data['next']:
                break
            page += 1
        # Now remove that Identifier from any people that it's disappeared from:
        Identifier.objects.filter(
            content_type=ContentType.objects.get_for_model(Person),
            scheme='za.org.pmg.api/member',
        ).exclude(object_id__in=pmg_member_ids).delete()

        # Now each person should have an identifier giving their PMG API.

        # Next, populate the attendance data cache:
        for pmg_member_id in pmg_member_ids:
            update_attendance_data_in_cache(pmg_member_id)

        # Populate committee attendance data in the cache:
        update_committee_attendance_data_in_cache()

        # Cache the ward councillor details from nearby.code4sa.org:
        for ward_area in Area.objects.filter(type__code='WD'):
            update_ward_councillor_data_in_cache(ward_area.name)
            time.sleep(SLEEP_BETWEEN_REQUESTS)
