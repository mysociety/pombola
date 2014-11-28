from django.conf.urls.defaults import patterns, include, url, handler404
from django.views.generic.simple import direct_to_template

from pombola.ghana.views import data_upload, info_page_upload

urlpatterns = patterns('',
    url(r'^intro$', direct_to_template, {'template': 'intro.html'}),
    url(r'^data/upload/mps/$', data_upload, name='data_upload'),
    url(r'^data/upload/info-page/$', info_page_upload, name='info_page_upload'),
)
