from django.conf.urls import patterns, url

from .views import wordcloud

urlpatterns = patterns(
    '',
    url(r'^wordcloud/$', wordcloud, name='wordcloud'),
    url(r'^wordcloud/(?P<max_entries>\d+)/$', 'wordcloud', name='wordcloud'),
    )
