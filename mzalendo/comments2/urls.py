from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url( r'^/', 'comments2.views.foo' ),
)
