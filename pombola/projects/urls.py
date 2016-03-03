from django.conf.urls import url

import views


urlpatterns = [
    url(r'^in/(?P<slug>[-\w]+)/', views.in_place, name='project_in_place'),
]
