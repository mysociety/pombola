from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from pombola.kenya.views import KEPersonDetail, KEPersonDetailAppearances

from pombola.experiments.views import ExperimentShare, ExperimentSurvey

from .views import (CountyPerformanceView, CountyPerformanceSenateSubmission,
    CountyPerformancePetitionSubmission, ExperimentRecordTimeOnPage,
    EXPERIMENT_DATA, ThanksTemplateView,
    YouthEmploymentView, YouthEmploymentSupportSubmission,
    YouthEmploymentCommentSubmission, ExperimentThanks,
    ShujaazFinalistsView
)

urlpatterns = patterns('',
    url(r'^shujaaz$', ShujaazFinalistsView.as_view(), name='shujaaz-finalists'),
    url(r'^shujaaz-voting$', TemplateView.as_view(template_name='shujaaz-voting.html'), name='shujaaz-voting'),
    url(r'^intro$',                TemplateView.as_view(template_name='intro.html') ),
    url(r'^register-to-vote$',     TemplateView.as_view(template_name='register-to-vote.html') ),
    url(r'^find-polling-station$', TemplateView.as_view(template_name='find-polling-station.html') ),
    url(r'^person/(?P<slug>[-\w]+)/$',
        KEPersonDetail.as_view(), name='person'),
    url(r'^person/(?P<slug>[-\w]+)/appearances/$',
        KEPersonDetailAppearances.as_view(sub_page='appearances'),
        name='person'),
)

# Create the two County Performance pages:

for experiment_slug in ('mit-county', 'mit-county-larger'):
    view_kwargs = {'experiment_slug': experiment_slug}
    view_kwargs.update(EXPERIMENT_DATA[experiment_slug])
    base_name = view_kwargs['base_view_name']
    base_path = r'^' + base_name
    urlpatterns.append(
        url(base_path + r'$',
            CountyPerformanceView.as_view(**view_kwargs),
            name=base_name)
    )

    for name, view in (
        ('senate', CountyPerformanceSenateSubmission),
        ('petition', CountyPerformancePetitionSubmission)):

        urlpatterns += (
            url(base_path + r'/{0}$'.format(name),
                view.as_view(**view_kwargs),
                name=(base_name + '-{0}-submission'.format(name))),
            url(base_path + r'/{0}/thanks$'.format(name),
                ThanksTemplateView.as_view(
                    base_view_name=base_name,
                    template_name=('county-performance-{0}-submission.html'.format(name))
                )),
        )

    urlpatterns += (
        url(base_path + r'/share',
            ExperimentShare.as_view(**view_kwargs),
            name=(base_name + '-share')),
        url(base_path + r'/survey',
            ExperimentSurvey.as_view(**view_kwargs),
            name=(base_name + '-survey')),
    )


# Create the Youth Employment Bill page:

for experiment_slug in ('youth-employment-bill',):
    view_kwargs = {'experiment_slug': experiment_slug}
    view_kwargs.update(EXPERIMENT_DATA[experiment_slug])
    base_name = view_kwargs['base_view_name']
    base_path = r'^' + base_name
    urlpatterns.append(
        url(base_path + r'$',
            YouthEmploymentView.as_view(**view_kwargs),
            name=base_name)
    )

    for name, view in (
        ('support', YouthEmploymentSupportSubmission),
        ('comment', YouthEmploymentCommentSubmission)):

        urlpatterns += (
            url(base_path + r'/{0}$'.format(name),
                view.as_view(**view_kwargs),
                name=(base_name + '-{0}-submission'.format(name))),
            url(base_path + r'/{0}/thanks$'.format(name),
                ThanksTemplateView.as_view(
                    base_view_name=base_name,
                    template_name=('youth-employment-{0}-submission.html'.format(name))
                )),
        )

    urlpatterns += (
        url(base_path + r'/share',
            ExperimentShare.as_view(**view_kwargs),
            name=(base_name + '-share')),
        url(base_path + r'/survey',
            ExperimentSurvey.as_view(**view_kwargs),
            name=(base_name + '-survey')),
        url(base_path + r'/input',
            ExperimentThanks.as_view(**view_kwargs),
            name=(base_name + '-input')),
        url(base_path + r'/time-on-page',
            ExperimentRecordTimeOnPage.as_view(**view_kwargs),
            name=(base_name + '-time-on-page')),
    )
