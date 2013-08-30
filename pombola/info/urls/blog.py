from django.conf.urls import patterns, include, url, handler404

from ..views import InfoBlogView, InfoBlogList, InfoBlogFeed

urlpatterns = patterns('',
    url(r'^$',                  InfoBlogList.as_view(), name='info_blog_list' ),
    url(r'^feed\.rss$',         InfoBlogFeed(),         name='info_blog_feed' ),
    url(r'^(?P<slug>[\w\-]+)$', InfoBlogView.as_view(), name='info_blog' ),
    url(r'^.*$',                handler404    ),
)
