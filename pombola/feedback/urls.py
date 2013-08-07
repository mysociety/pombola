from django.conf.urls import patterns, include, url

urlpatterns = patterns('pombola.feedback.views',
    url( r'^$',       'add',    name='feedback_add'    ),
)
