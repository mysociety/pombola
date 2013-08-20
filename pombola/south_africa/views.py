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

        # I don't really want to add a method onto the Organisation object just to
        # get the postal address of these when it's so nice and general.
        # Tacking on an attribute like this is not lovely, but it does get it there
        # without having to modify core for the sake of ZA. Another possibility
        # would be to use a proxy model, but then we couldn't get it as an attribute
        # of the place above.
        for office in context['nearest_offices']:
            office.postal_addresses = office.contacts.filter(kind__slug='address')
            office.related_positions = models.Position.objects.filter(organisation=office)

        return context
