from django.conf.urls.defaults import patterns, include, url
from hansard.views import IndexView

urlpatterns = patterns('',
    url( r'^$', IndexView.as_view() ),
)
