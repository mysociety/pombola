from django.contrib.gis.geos import Point

import mapit

from pombola.core import models
from pombola.core.views import PlaceDetailView

class LatLonDetailView(PlaceDetailView):
    template_name = 'south_africa/latlon_detail_view.html'

    def get_object(self):
        # FIXME - handle bad args better.
        lat = float(self.kwargs['lat'])
        lon = float(self.kwargs['lon'])

        self.location = Point(lon, lat)

        areas = mapit.models.Area.objects.by_location(self.location)

        # FIXME - Handle not finding a province or getting more than one.
        province = models.Place.objects.get(mapit_area__in=areas, kind__slug='province')

        return province

    def get_context_data(self, **kwargs):
        context = super(LatLonDetailView, self).get_context_data(**kwargs)
        context['location'] = self.location

        nearest_offices_locations = (
            models.Place.objects
            .filter(kind__slug='constituency-office').distance(self.location)
            .order_by('distance')
            )

        parties = models.Organisation.objects.all().active_parties()

        office_lists = [
            nearest_offices_locations.filter(
                organisation__org_rels_as_b__organisation_a=party,
                organisation__org_rels_as_b__kind__name='has_office',
                )
            for party in parties
            ]

        context['nearest_offices'] = [x[0].organisation for x in office_lists if x]
        return context

def latlon(request, lat, lon):
    lat = float(lat)
    lon = float(lon)
    
    location = Point(lon, lat)

    areas = mapit.models.Area.objects.by_location(location)

    # FIXME - Handle not finding a province or getting more than one.
    province = models.Place.objects.get(mapit_area__in=areas, kind__slug='province')

    province_positions = province.position_set.all().currently_active()

    na_positions = province_positions.filter(organisation__slug='national-assembly')
    ncop_positions = province_positions.filter(organisation__slug='ncop')

    # na_members = models.Person.objects.filter(
    #     position__place=province,
    #     position__organisation__slug='national-assembly',
    #     )

    # ncop_members = models.Person.objects.filter(
    #     position__place=province,
    #     position__organisation__slug='ncop',
    #     )

    nearest_offices = (
        models.Place.objects
        .filter(kind__slug='constituency-office').distance(location)
        .order_by('distance')
        )

    parties = models.Organisation.objects.all().active_parties()

    office_lists = [
        nearest_offices.filter(
            organisation__org_rels_as_b__organisation_a=party,
            organisation__org_rels_as_b__kind__name='has_office',
            )
        for party in parties
        ]

    offices = [x[0] for x in office_lists if x]

    # FIXME - Constituency areas.

    import pdb;pdb.set_trace()
