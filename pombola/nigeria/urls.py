from django.conf.urls import patterns, include, url

from .views import NGHomeView, SearchPollUnitNumberView

urlpatterns = patterns('',
    url(r'^$', NGHomeView.as_view(), name='home'),
    url(r'^search/poll-unit-number/', SearchPollUnitNumberView.as_view(), name='search-poll-unit-number' )
)
