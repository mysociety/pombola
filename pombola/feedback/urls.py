from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('feedback.views',
    url( r'^$',       'add',    name='feedback_add'    ),
)
