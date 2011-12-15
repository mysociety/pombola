from django.conf.urls.defaults import patterns, include, url
from hansard.views import IndexView, SittingView

urlpatterns = patterns('hansard.views',
    url( r'^$', IndexView.as_view(), name="index" ),

    # not the final URL structure - but something to start work with
    url( r'^sitting/(?P<pk>\d+)/', SittingView.as_view(), name="sitting_view" ),
    
    # views for a specific person
    url( r'^person/(?P<slug>[\w\-]+)/summary/', 'person_summary', name='person_summary' ),
    # url( r'^person/(?P<slug>[\w\-]+)/',         'person_entries', name='person_entries' ),

)
