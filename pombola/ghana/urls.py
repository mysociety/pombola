from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

from .views import data_upload, info_page_upload

urlpatterns = patterns('',
    url(r'^intro$', TemplateView.as_view(template_name='intro.html')),
    url(r'^data/upload/mps/$', data_upload, name='data_upload'),
    url(r'^data/upload/info-page/$', info_page_upload, name='info_page_upload'),
    url('', include('django.contrib.auth.urls')),
)
