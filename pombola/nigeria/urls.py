from django.conf.urls import patterns, url

from .views import NGHomeView, NGSearchView


urlpatterns = patterns('',
    url(r'^$', NGHomeView.as_view(), name='home'),
    url(r'^search/$', NGSearchView.as_view(), name='core_search'),
)
