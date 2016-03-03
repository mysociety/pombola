from django.conf.urls import url
from pombola.hansard.views import (
    IndexView,
    person_summary,
    PersonAllAppearancesView,
    SittingView,
    )


urlpatterns = [
    url( r'^$', IndexView.as_view(), name="index" ),

    # not the final URL structure - but something to start work with
    # url( r'^sitting/(?P<pk>\d+)/', SittingView.as_view(), name="sitting_view" ),

    # Try to make the url human readable
    # sitting/<venue>/<start_date>[-<start_time>]/
    # sitting/main_chamber/2011-12-03
    # sitting/main_chamber/2011-12-03-14-00-00
    url(
        r'^sitting/(?P<venue_slug>[\w\-]+)/(?P<start_date_and_time>\d{4}-\d{2}-\d{2}(?:-\d{2}-\d{2}-\d{2})?)',
        SittingView.as_view(),
        name="sitting_view"
    ),



    # views for a specific person
    url(r'^person/(?P<slug>[\w\-]+)/summary/', person_summary, name='person_summary'),
    # url( r'^person/(?P<slug>[\w\-]+)/',         'person_entries', name='person_entries' ),

    # 'Show All' page for a specific person
    url(
        r'^person/(?P<slug>[\w\-]+)/appearances/',
        PersonAllAppearancesView.as_view(),
        name='person_appearances_all',
    ),
]
