from django.conf.urls.defaults import patterns, include, url, handler404

import views

urlpatterns = patterns('',
    url(r'^$',                  views.InfoPageView.as_view(), { 'slug': 'index' } ),
    url(r'^(?P<slug>[\w\-]+)$', views.InfoPageView.as_view(), name='info_page' ),
    url(r'^.*$',                handler404    ),
)
