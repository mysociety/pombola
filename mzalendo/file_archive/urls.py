from django.conf.urls.defaults import patterns, include, url, handler404

import views

urlpatterns = patterns('',
    url( r'^(?P<slug>[\w\-]+)$', views.redirect_to_file, name='file_archive' ),
)
