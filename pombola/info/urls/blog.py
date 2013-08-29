from django.conf.urls import patterns, include, url, handler404

from ..views import InfoBlogView, InfoBlogList

urlpatterns = patterns('',
    url(r'^$',                  InfoBlogList.as_view(), { 'slug': 'index' } ),
    url(r'^(?P<slug>[\w\-]+)$', InfoBlogView.as_view(), name='info_blog' ),
    url(r'^.*$',                handler404    ),
)
