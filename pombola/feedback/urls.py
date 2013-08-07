from django.conf.urls import patterns, include, url

urlpatterns = patterns('feedback.views',
    url( r'^$',       'add',    name='feedback_add'    ),
)
