from django.conf.urls import patterns, include, url

from pombola.core.views import PersonDetailSub
from pombola.south_africa.views import LatLonDetailView,SAPlaceDetailSub

urlpatterns = patterns('pombola.south_africa.views',
    url(r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/', LatLonDetailView.as_view(), name='latlon'),
    url(r'^place/(?P<slug>[-\w]+)/places/', SAPlaceDetailSub.as_view(), {'sub_page': 'places'}, name='place_places'),
)
