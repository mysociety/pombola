from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from .views import wordcloud

urlpatterns = patterns(
    '',
    url(r'^wordcloud/$', wordcloud, name='wordcloud'),
    url(r'^wordcloud/(?P<max_entries>\d+)/$', wordcloud, name='wordcloud'),

    # Temporary redirects of old urls
    url(r'^tagcloud/$',
        RedirectView.as_view(pattern_name='wordcloud', permanent=True)),
    url(r'^tagcloud/(?P<max_entries>\d+)/$',
        RedirectView.as_view(pattern_name='wordcloud', permanent=True)),
    )
