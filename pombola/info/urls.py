from django.conf.urls.defaults import patterns, include, url, handler404

import views

urlpatterns = patterns('',
    url(r'^$',                  views.info_page ),
    url(r'^(?P<slug>[\w\-]+)$', views.info_page, name='info_page' ),
    url(r'^.*$',                handler404    ),
)
