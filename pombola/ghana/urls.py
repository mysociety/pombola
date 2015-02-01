from django.conf.urls import patterns, include, url, handler404
from django.views.generic import TemplateView
import django.contrib.auth.views


from .views import data_upload, info_page_upload

urlpatterns = patterns('',
    url(r'^intro$', TemplateView.as_view(template_name='intro.html')),
    url(r'^data/upload/mps/$', data_upload, name='data_upload'),
    url(r'^data/upload/info-page/$', info_page_upload, name='info_page_upload'),
    
    #auth views
    url(r'^accounts/login$', django.contrib.auth.views.login, name='login'),
    url(r'^accounts/logut$', django.contrib.auth.views.logout, name='logout'),
    #url(r'^accounts/register$', registration.backends.simple.urls, name='register'),


)
