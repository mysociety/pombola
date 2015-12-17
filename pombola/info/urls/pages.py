from django.conf.urls import patterns, url, handler404

from ..views import InfoPageView


urlpatterns = patterns('',
    url(r'^$',                  InfoPageView.as_view(), { 'slug': 'index' } ),
    url(r'^(?P<slug>[\w\-]+)$', InfoPageView.as_view(), name='info_page' ),
    url(r'^.*$',                handler404    ),
)
