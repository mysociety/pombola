from django.conf.urls import url

from .views import NGHomeView, NGSearchView


urlpatterns = [
    url(r'^$', NGHomeView.as_view(), name='home'),
    url(r'^search/$', NGSearchView.as_view(), name='core_search'),
]
