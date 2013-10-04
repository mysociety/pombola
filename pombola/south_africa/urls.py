from django.conf.urls import patterns, include, url

from pombola.south_africa.views import LatLonDetailView, SAPlaceDetailSub, SAOrganisationDetailView
from pombola.core.urls import organisation_patterns

# Override the organisation url so we can vary it depending on the organisation type.
for index, pattern in enumerate(organisation_patterns):
    if pattern.name == 'organisation':
        organisation_patterns[index] = url(r'^organisation/(?P<slug>[-\w]+)/$', SAOrganisationDetailView.as_view(), name='organisation')

urlpatterns = patterns('pombola.south_africa.views',
    url(r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/', LatLonDetailView.as_view(), name='latlon'),
    url(r'^place/(?P<slug>[-\w]+)/places/', SAPlaceDetailSub.as_view(), {'sub_page': 'places'}, name='place_places'),
)
