from django.conf.urls.defaults import patterns, include, url, handler404
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'^intro$', direct_to_template, {'template': 'intro.html'} ),
)
