from django.conf.urls.defaults import patterns, include, url
from hansard.views import IndexView, SittingView

urlpatterns = patterns('hansard.views',
    url( r'^$', IndexView.as_view() ),

    # not the final URL structure - but something to start work with
    url( r'^sitting/(?P<pk>\d+)/', SittingView.as_view(), name="sitting_view" )

)
