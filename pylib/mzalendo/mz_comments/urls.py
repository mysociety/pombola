from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns( 'mz_comments.views',
    (r'^for/(?P<module_name>[a-z]+)/(?P<slug>[\w\-]+)/add/', 'add' ),
    (r'^for/(?P<module_name>[a-z]+)/(?P<slug>[\w\-]+)/',     'list_for' ),
)

urlpatterns += patterns('',
    (r'^', include('django.contrib.comments.urls') ),
)

