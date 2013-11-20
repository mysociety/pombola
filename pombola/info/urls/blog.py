from django.conf.urls import patterns, include, url, handler404

from ..views import InfoBlogView, InfoBlogList, InfoBlogFeed, InfoBlogCategory

urlpatterns = patterns('',
    url(r'^$', InfoBlogList.as_view(), name='info_blog_list'),
    url(r'^category/(?P<slug>[\w\-]+)$', InfoBlogCategory.as_view(), name='info_blog_category'),
    url(r'^feed\.rss$', InfoBlogFeed(), name='info_blog_feed'),
    url(r'^(?P<slug>[\w\-]+)$', InfoBlogView.as_view(), name='info_blog'),
    url(r'^.*$', handler404),
)
