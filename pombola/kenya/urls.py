from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from pombola.kenya.views import KEPersonDetail

from .views import (CountyPerformanceView, CountyPerformanceSenateSubmission,
    CountyPerformancePetitionSubmission, CountyPerformanceShare,
    CountyPerformanceSurvey)

urlpatterns = patterns('',
    url(r'^intro$',                TemplateView.as_view(template_name='intro.html') ),
    url(r'^register-to-vote$',     TemplateView.as_view(template_name='register-to-vote.html') ),
    url(r'^find-polling-station$', TemplateView.as_view(template_name='find-polling-station.html') ),
    url(r'^person/(?P<slug>[-\w]+)/$',
        KEPersonDetail.as_view(), name='person'),
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

urlpatterns += (
    url(r'county-performance/share',
        CountyPerformanceShare.as_view(),
        name='county-performance-share'),
    url(r'county-performance/survey',
        CountyPerformanceSurvey.as_view(),
        name='county-performance-survey'),
)
