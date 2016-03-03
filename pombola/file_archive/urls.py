from django.conf.urls import url

import views


urlpatterns = [
    url( r'^(?P<slug>[\w\-]+)$', views.redirect_to_file, name='file_archive' ),
]
