from django.conf.urls import patterns, url

urlpatterns = patterns('pombola.map.views',
    url(r'^$', 'home', name='map-home'),
)
