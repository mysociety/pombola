from django.contrib.gis.geos import Point

import mapit

from pombola.core import models

def latlon(request, lat, lon):
    lat = float(lat)
    lon = float(lon)
    
    location = Point(lon, lat)

    areas = mapit.models.Area.objects.by_location(location)

    # FIXME - Handle not finding a province or getting more than one.
    province = models.Place.objects.get(mapit_area__in=areas, kind__slug='province')
    
    na_members = models.Person.objects.filter(
        position__place=province,
        position__organisation__slug='national-assembly',
        )

    ncop_members = models.Person.objects.filter(
        position__place=province,
        position__organisation__slug='ncop',
        )

    nearest_offices = models.Place.objects.filter(kind__slug='constituency-office').distance(location).order_by('distance')

    # FIXME - Need to limit to active parties.
    parties = models.Organisation.objects.filter(kind__slug='party')

    office_lists = [
        nearest_offices.filter(
            organisation__org_rels_as_b__organisation_a=party,
            organisation__org_rels_as_b__kind__name='has_office',
            )
        for party in parties
        ]

    offices = [x[0] if x else None for x in office_lists]

    import pdb;pdb.set_trace()

