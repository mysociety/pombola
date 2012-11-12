from django.conf.urls.defaults import patterns, include, url, handler404
from django.views.generic.simple import direct_to_template

from odekro.views import data_upload

urlpatterns = patterns('',
    url(r'^intro$', direct_to_template, {'template': 'intro.html'}),
    url(r'^data_upload/$', data_upload, name='data_upload'),
)
