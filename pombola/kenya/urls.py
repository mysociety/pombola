from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from .views import CountyPerformanceView

urlpatterns = patterns('',
    url(r'^intro$',                TemplateView.as_view(template_name='intro.html') ),
    url(r'^register-to-vote$',     TemplateView.as_view(template_name='register-to-vote.html') ),
    url(r'^find-polling-station$', TemplateView.as_view(template_name='find-polling-station.html') ),
    url(r'^county-performance', CountyPerformanceView.as_view()),
)
