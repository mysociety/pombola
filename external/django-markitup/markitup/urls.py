from django.conf.urls.defaults import *

from markitup.views import apply_filter

urlpatterns = patterns(
    '',
    url(r'preview/$', apply_filter, name='markitup_preview')
    )
