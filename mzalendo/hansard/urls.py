from django.conf.urls.defaults import patterns, include, url, handler404

import views

urlpatterns = patterns('',
    url(r'^$', views.default),
)
