from django.conf.urls import url
from django.views.generic import ListView, RedirectView, TemplateView
from pombola.core import models
from pombola.kenya.views import (
    KEPersonDetail,
    KEPersonDetailAppearances,
    KEPersonDetailExperience,
    )

from pombola.experiments.views import ExperimentShare, ExperimentSurvey

from .views import (CountyPerformanceView, CountyPerformanceSenateSubmission,
    CountyPerformancePetitionSubmission, ExperimentRecordTimeOnPage,
    EXPERIMENT_DATA, ThanksTemplateView,
    YouthEmploymentView, YouthEmploymentSupportSubmission,
    YouthEmploymentCommentSubmission, ExperimentThanks,
    YouthEmploymentInputSubmission, YouthEmploymentBillView,
    ShujaazFinalists2014View, ShujaazFinalists2015View,
)
from .views_iebc_office_locator import (
    OfficeDetailView, OfficeSingleSelectView
)


urlpatterns = [
    url(r'^shujaaz$',
        RedirectView.as_view(
            pattern_name='shujaaz-finalists-2015',
            permanent=False
        ),
        name='shujaaz-redirect'
    ),
    url(r'^shujaaz/2015$', ShujaazFinalists2015View.as_view(), name='shujaaz-finalists-2015'),
    url(r'^shujaaz/2014$', ShujaazFinalists2014View.as_view(), name='shujaaz-finalists-2014'),
    url(r'^shujaaz-voting$', TemplateView.as_view(template_name='shujaaz-voting.html'), name='shujaaz-voting'),
    url(r'^intro$',                TemplateView.as_view(template_name='intro.html') ),
    url(r'^register-to-vote$',     TemplateView.as_view(template_name='register-to-vote.html') ),
    url(r'^find-polling-station$', TemplateView.as_view(template_name='find-polling-station.html') ),
    url(r'^women/$', TemplateView.as_view(template_name='women.html') ),
    url(r'^person/all/$',
        ListView.as_view(model=models.Person),
        name='person_list'),
    url(r'^person/(?P<slug>[-\w]+)/$',
        KEPersonDetail.as_view(), name='person'),
    url(r'^person/(?P<slug>[-\w]+)/appearances/$',
        KEPersonDetailAppearances.as_view(sub_page='appearances'),
        name='person'),
    url(r'^person/(?P<slug>[-\w]+)/experience/$',
        KEPersonDetailExperience.as_view(sub_page='experience'),
        name='person'),
    url('^info/political-parties$', RedirectView.as_view(
            pattern_name='organisation_kind',
            permanent=False,
            ),
        {'slug': 'party'},
        ),
    url(r'^iebc-office-lookup$',
        OfficeSingleSelectView.as_view(),
        name='iebc-offices-single-select'
    ),
    url(r'^iebc-office$',
        OfficeDetailView.as_view(),
        name='iebc-office'
    ),
]

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

for experiment_slug in (
        'youth-employment-bill',
        'youth-employment-bill-generic-no-randomization',
):
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
        ('input', YouthEmploymentInputSubmission),
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
        url(base_path + r'/bill',
            YouthEmploymentBillView.as_view(**view_kwargs),
            name=(base_name + '-bill')),
        url(base_path + r'/input',
            ExperimentThanks.as_view(**view_kwargs),
            name=(base_name + '-input')),
        url(base_path + r'/time-on-page',
            ExperimentRecordTimeOnPage.as_view(**view_kwargs),
            name=(base_name + '-time-on-page')),
    )
