from django.conf.urls import patterns, include, url

from django.views.generic import ListView, TemplateView



urlpatterns = patterns( '',
    url( r'^random$', TemplateView.as_view(template_name='spinner/random.html'), name='spinner_random' ),
)
