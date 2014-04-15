from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from .views import (CountyPerformanceView, CountyPerformanceSenateSubmission,
    CountyPerformancePetitionSubmission)

urlpatterns = patterns('',
    url(r'^intro$',                TemplateView.as_view(template_name='intro.html') ),
    url(r'^register-to-vote$',     TemplateView.as_view(template_name='register-to-vote.html') ),
    url(r'^find-polling-station$', TemplateView.as_view(template_name='find-polling-station.html') ),
    url(r'^county-performance$', CountyPerformanceView.as_view(), name='county-performance'),
)

for name, view in (
        ('senate', CountyPerformanceSenateSubmission),
        ('petition', CountyPerformancePetitionSubmission)):

    urlpatterns += (
        url(r'^county-performance/{0}$'.format(name),
            view.as_view(),
            name='county-performance-{0}-submission'.format(name)),
        url(r'^county-performance/{0}/thanks$'.format(name),
            TemplateView.as_view(
                template_name='county-performance-{0}-submission.html'.format(name))),
    )
