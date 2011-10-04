from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^markitup/', include('markitup.urls')),
    )
