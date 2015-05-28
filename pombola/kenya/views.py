# Create your views here.
# -*- coding: utf-8 -*-

from random import randint, shuffle
import sys

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView

from .forms import CountyPerformancePetitionForm, CountyPerformanceSenateForm

from pombola.core.models import Person
from pombola.core.views import PersonDetail, PersonDetailSub
from pombola.experiments.views import (
    ExperimentViewDataMixin, ExperimentFormSubmissionMixin,
    sanitize_parameter
)
from pombola.hansard.views import HansardPersonMixin
from pombola.kenya import shujaaz

EXPERIMENT_DATA = {
    'mit-county': {
        'session_key_prefix': 'MIT',
        'base_view_name': 'county-performance',
        'pageview_label': 'county-performance',
        'template_prefix': 'county',
        'experiment_key': None,
        'qualtrics_sid': 'SV_5hhE4mOfYG1eaOh',
        'variants': ('o', 't', 'n', 'os', 'ts', 'ns'),
        'demographic_keys': {
            'g': ('m', 'f'),
            'agroup': ('under', 'over'),
        },
    },
    'mit-county-larger': {
        'session_key_prefix': 'MIT2',
        'base_view_name': 'county-performance-2',
        'pageview_label': 'county-performance-2',
        'template_prefix': 'county',
        'experiment_key': settings.COUNTY_PERFORMANCE_EXPERIMENT_KEY,
        'qualtrics_sid': 'SV_5hhE4mOfYG1eaOh',
        'variants': ('o', 't', 'n', 'os', 'ts', 'ns'),
        'demographic_keys': {
            'g': ('m', 'f'),
            'agroup': ('under', 'over'),
        },
    }
}


class KEPersonDetail(HansardPersonMixin, PersonDetail):

    def get_context_data(self, **kwargs):
        context = super(KEPersonDetail, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":3"

        constituencies = self.object.constituencies().filter(
            budget_entries__organisation='Constituencies Development Fund'
        ).select_related()

        # We only retrieve one budget because we only really care about the
        # latest. budgets() are default sorted by date of the budget session.
        cdf_budget_constituencies = [
            {'constituency': c, 'budget': c.budgets()[0]}
            for c in constituencies
        ]

        context['cdf_budget_constituencies'] = cdf_budget_constituencies

        shujaaz_finalist = shujaaz.FINALISTS_DICT.get(self.object.pk)
        if shujaaz_finalist:
            context['shujaaz_finalist'] = shujaaz_finalist

        return context


class KEPersonDetailAppearances(HansardPersonMixin, PersonDetailSub):

    def get_context_data(self, **kwargs):
        context = super(KEPersonDetailAppearances, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":5"
        context['lifetime_summary'] = context['hansard_entries'] \
            .monthly_appearance_counts()
        return context


class CountyPerformanceView(ExperimentViewDataMixin, TemplateView):
    """This view displays a page about county performance with calls to action

    There are some elements of the page that are supposed to be
    randomly ordered.  There are also three major variants of the
    page that include different information."""

    template_name = 'county-performance.html'

    def get_context_data(self, **kwargs):
        context = super(CountyPerformanceView, self).get_context_data(**kwargs)
        context['petition_form'] = CountyPerformancePetitionForm()
        context['senate_form'] = CountyPerformanceSenateForm()

        # Add URLs based on the experiment that's being run:
        context['survey_url'] = reverse(self.base_view_name + '-survey')
        context['base_url'] = reverse(self.base_view_name)
        context['share_url'] = reverse(self.base_view_name + '-share')
        context['petition_submission_url'] = \
            reverse(self.base_view_name + '-petition-submission')
        context['senate_submission_url'] = \
            reverse(self.base_view_name + '-senate-submission')
        context['experiment_key'] = self.experiment_key

        data = self.sanitize_data_parameters(
            self.request,
            self.request.GET
        )
        variant = data['variant']

        # If there's no user key in the session, this is the first
        # page view, so record any parameters indicating where the
        # user came from (Facebook demographics or the 'via' parameter
        # from a social share):
        if self.qualify_key('user_key') not in self.request.session:
            self.request.session[self.qualify_key('user_key')] = str(randint(0, sys.maxint))
            for k in ('variant', 'via', 'g', 'agroup'):
                self.request.session[self.qualify_key(k)] = data[k]

        # Add those session parameters to the context for building the
        # Qualtrics survey URL
        context.update(self.get_session_data())

        # Only record a page view event (and set the variant) if this
        # was a page picked by Google Analytics's randomization -
        # otherwise we'd get a spurious page view before a particular
        # variant is reloaded:
        if 'utm_expid' in self.request.GET:
            self.request.session[self.qualify_key('variant')] = variant
            # Now create the page view event:
            self.create_event({'category': 'page',
                               'action': 'view',
                               'label': self.pageview_label})

        context['show_social_context'] = variant in ('ns', 'ts', 'os')
        context['show_threat'] = (variant[0] == 't')
        context['show_opportunity'] = (variant[0] == 'o')

        context['share_partials'] = [
            '_share_twitter.html',
            '_share_facebook.html',
        ]
        shuffle(context['share_partials'])

        context['major_partials'] = [
            '_county_share.html',
            '_county_petition.html',
            '_county_senate.html',
        ]
        shuffle(context['major_partials'])

        return context


class CountyPerformanceSenateSubmission(ExperimentFormSubmissionMixin,
                                        FormView):
    """A view for handling submissions of comments for the senate"""

    template_name = 'county-performance.html'
    form_class = CountyPerformanceSenateForm
    form_key = 'senate'

    def get_success_url(self):
        return '/{0}/senate/thanks'.format(self.base_view_name)

    def create_feedback_from_form(self, form):
        new_comment = form.cleaned_data.get('comments', '').strip()
        self.create_feedback(form, comment=new_comment)


class CountyPerformancePetitionSubmission(ExperimentFormSubmissionMixin,
                                          FormView):
    """A view for handling a petition signature"""

    template_name = 'county-performance.html'
    form_class = CountyPerformancePetitionForm
    form_key = 'petition'

    def get_success_url(self):
        return '/{0}/petition/thanks'.format(self.base_view_name)

    def create_feedback_from_form(self, form):
        new_comment = form.cleaned_data.get('name', '').strip()
        self.create_feedback(form,
                             comment=new_comment,
                             email=form.cleaned_data.get('email'))


class CountyPerformanceShare(ExperimentViewDataMixin, RedirectView):
    """For recording & enacting Facebook / Twitter share actions"""

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        social_network = sanitize_parameter(
            key='n',
            parameters=self.request.GET,
            allowed_values=('facebook', 'twitter'))
        share_key = "{0:x}".format(randint(0, sys.maxint))
        self.create_event({'category': 'share-click',
                           'action': 'click',
                           'label': social_network,
                           'share_key': share_key})
        path = reverse(self.base_view_name)
        built = self.request.build_absolute_uri(path)
        built += '?via=' + share_key
        url_parameter = urlquote(built, safe='')
        url_formats = {
            'facebook': "https://www.facebook.com/sharer/sharer.php?u={0}",
            'twitter': "http://twitter.com/share?url={0}"}
        return url_formats[social_network].format(url_parameter)


class CountyPerformanceSurvey(ExperimentViewDataMixin, RedirectView):
    """For redirecting to the Qualtrics survey"""

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        self.create_event({'category': 'take-survey',
                           'action': 'click',
                           'label': 'take-survey'})
        prefix = self.session_key_prefix
        sid = self.qualtrics_sid
        url = "http://survey.az1.qualtrics.com/SE/?SID={0}&".format(sid)
        url += "&".join(
            k + "=" + self.request.session.get(prefix + ':' + k, '?')
            for k in ('user_key', 'variant', 'g', 'agroup'))
        return url


class ThanksTemplateView(TemplateView):

    base_view_name = None

    def get_context_data(self, **kwargs):
        context = super(ThanksTemplateView, self).get_context_data(**kwargs)
        context['base_url'] = reverse(self.base_view_name)
        return context


class ShujaazFinalistsView(TemplateView):
    template_name = 'shujaaz.html'

    def get_context_data(self, **kwargs):
        context = super(ShujaazFinalistsView, self).get_context_data(**kwargs)

        def populate_person(f):
            finalist = dict(f)
            finalist['person'] = Person.objects.get(pk=finalist['person'])
            return finalist

        finalists = [populate_person(f) for f in shujaaz.FINALISTS]
        half = len(finalists) / 2
        context['finalists_column_1'] = finalists[:half]
        context['finalists_column_2'] = finalists[half:]
        return context
