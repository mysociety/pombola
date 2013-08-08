from django.conf.urls import patterns, include, url

urlpatterns = patterns('pombola.south_africa.views',
    url( r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/', 'latlon', name='latlon'),
    # There are no overridden urls for South Africa, yet....
)
