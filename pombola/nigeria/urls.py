from django.conf.urls import patterns, include, url

from .views import SearchPollUnitNumberView

urlpatterns = patterns('',
    url(r'^search/poll-unit-number/', SearchPollUnitNumberView.as_view(), name='search-poll-unit-number' )
)
