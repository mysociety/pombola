from django.conf.urls import patterns, include, url

from .views import tagcloud

urlpatterns = patterns('',
    url( r'^tagcloud/$', tagcloud, name='tagcloud'),
#     url( r'^tagcloud/(?P<n>\d+)/$', 'tagcloud', name='tagcloud'),
    )
