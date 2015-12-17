from django.conf.urls import patterns, url

import views


urlpatterns = patterns('',
    url( r'^(?P<slug>[\w\-]+)$', views.redirect_to_file, name='file_archive' ),
)
