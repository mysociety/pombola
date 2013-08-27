from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

import mapit

from pombola.core import models
from pombola.core.views import PlaceDetailView

class LatLonDetailView(PlaceDetailView):
    template_name = 'south_africa/latlon_detail_view.html'

    # Using 25km as the default, as that's what's used on MyReps.
    constituency_office_search_radius = 25

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

        context['office_search_radius'] = self.constituency_office_search_radius

        context['nearest_offices'] = nearest_offices = (
            models.Place.objects
            .filter(kind__slug='constituency-office')
            .distance(self.location)
            .filter(location__distance_lte=(self.location, D(km=self.constituency_office_search_radius)))
            .order_by('distance')
            )

        # I don't really want to add a method onto the Place object just to
        # get the postal address of these when it's so nice and general.
        # Tacking on an attribute like this is not lovely, but it does get it there
        # without having to modify core for the sake of ZA. Another possibility
        # would be to use a proxy model.

        for office in nearest_offices:
            office.postal_addresses = office.organisation.contacts.filter(kind__slug='address')
            office.related_positions = models.Position.objects.filter(organisation=office.organisation)

        return context
