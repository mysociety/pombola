from django.conf.urls import patterns, url

urlpatterns = patterns('pombola.feedback.views',
    url( r'^$',       'add',    name='feedback_add'    ),
)
