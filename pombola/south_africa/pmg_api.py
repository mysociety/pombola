import json
import re
from urlparse import urlparse

from django.core.cache import caches

import requests

from pombola.core.models import Person

# Cache API results for 5 days, since it sometimes goes down for days
# at a time; we try to update the data on a nightly basis:
CACHE_TTL_SECONDS = 60 * 60 * 24 * 5

# For requests to external APIs, timeout after 3 seconds:
API_REQUESTS_TIMEOUT = 3.05


class AttendanceAPIDown(Exception):
    pass


def get_person_from_pa_url(url):
    parsed = urlparse(url)
    m = re.search(r'^/person/(?P<slug>[-\w]+)/', parsed.path)
    if not m:
        raise ValueError("Malformed URL '{0}'".format(url))
    slug = m.group('slug')
    return Person.objects.get(slug=slug)


def update_or_create_pmg_api_identifier(person, pmg_api_member_id):
    scheme = 'za.org.pmg.api/member'
    person.identifiers.update_or_create(
        scheme=scheme,
        defaults={'identifier': pmg_api_member_id}
    )


def get_attendance_data_url(member_id):
    return "http://api.pmg.org.za/member/{0}/attendance/".format(member_id)


def get_committee_attendance_data_url():
    return 'https://api.pmg.org.za/committee-meeting-attendance/summary/'


def get_ward_councillors_data_url(ward_name):
    return 'http://nearby.code4sa.org/councillor/ward-{0}.json'.format(
        ward_name)


def get_paginated_api_results(initial_url):
    next_url = initial_url

    results = []
    while next_url:
        try:
            resp = requests.get(next_url, timeout=API_REQUESTS_TIMEOUT)
        except requests.exceptions.RequestException:
            raise AttendanceAPIDown

        data = json.loads(resp.text)
        results.extend(data.get('results'))

        next_url = data.get('next')

    return results


def update_attendance_data_in_cache(member_id):
    attendance_url = get_attendance_data_url(member_id)
    cache = caches['pmg_api']
    data = get_paginated_api_results(attendance_url)
    cache.set(attendance_url, data, CACHE_TTL_SECONDS)


def update_committee_attendance_data_in_cache():
    attendance_url = get_committee_attendance_data_url()
    cache = caches['pmg_api']
    data = get_paginated_api_results(attendance_url)
    cache.set(attendance_url, data, CACHE_TTL_SECONDS)


def update_ward_councillor_data_in_cache(ward_name):
    nearby_url = get_ward_councillors_data_url(ward_name)
    r = requests.get(nearby_url)
    cache = caches['pmg_api']
    cache.set(nearby_url, r.json(), CACHE_TTL_SECONDS)
