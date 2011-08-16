from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',    
    (r'^for/(?P<module_name>[a-z]+)/(?P<slug>[\w\-]+)/',               'mz_comments.views.list_for' ),
    (r'^', include('django.contrib.comments.urls')),
)

