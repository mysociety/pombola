from django.conf.urls import patterns, url, include

from pombola.ghana.views import data_upload, info_page_upload

urlpatterns = patterns('',
    url(r'^data/upload/mps/$', data_upload, name='data_upload'),
    url(r'^data/upload/info-page/$', info_page_upload, name='info_page_upload'),
    url('', include('django.contrib.auth.urls')),
)
