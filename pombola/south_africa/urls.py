from django.conf.urls import patterns, include, url

from pombola.south_africa.views import LatLonDetailView

urlpatterns = patterns('pombola.south_africa.views',
    url( r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/', LatLonDetailView.as_view(), name='latlon'),
)
