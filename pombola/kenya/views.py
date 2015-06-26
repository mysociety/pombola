# Create your views here.
# -*- coding: utf-8 -*-

import random
import json
import sys

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView

from .forms import (
    CountyPerformancePetitionForm, CountyPerformanceSenateForm,
    YouthEmploymentCommentForm, YouthEmploymentSupportForm,
    YouthEmploymentInputForm
)

from pombola.core.models import Person
from pombola.core.views import PersonDetail, PersonDetailSub
from pombola.experiments.views import (
    ExperimentViewDataMixin, ExperimentFormSubmissionMixin
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
        'major_partials': [
            '_county_share.html',
            '_county_petition.html',
            '_county_senate.html',
        ],
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
        'major_partials': [
            '_county_share.html',
            '_county_petition.html',
            '_county_senate.html',
        ],
    },
    'youth-employment-bill': {
        'session_key_prefix': 'MIT3',
        'base_view_name': 'youth-employment',
        'pageview_label': 'youth-employment',
        'template_prefix': 'youth',
        'experiment_key': settings.YOUTH_EMPLOYMENT_BILL_EXPERIMENT_KEY,
        'qualtrics_sid': 'SV_ebVXgzAevcuo2sB',
        'variants': ('y', 'n'),
        'demographic_keys': {
            'g': ('m', 'f'),
            'agroup': ('under', 'over'),
            'pint': ('hi', 'lo'),
        },
        'major_partials': [
            '_youth_share.html',
            '_youth_comment.html',
            '_youth_support.html',
            '_youth_input.html'
        ],

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


class MITExperimentView(ExperimentViewDataMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super(MITExperimentView, self).get_context_data(**kwargs)

        context['experiment_key'] = self.experiment_key
        context['base_url'] = reverse(self.base_view_name)
        context['survey_url'] = reverse(self.base_view_name + '-survey')
        context['share_url'] = reverse(self.base_view_name + '-share')

        data = self.sanitize_data_parameters(
            self.request,
            self.request.GET
        )
        context['variant'] = variant = data['variant']

        # If there's no user key in the session, this is the first
        # page view, so record any parameters indicating where the
        # user came from (Facebook demographics or the 'via' parameter
        # from a social share) and a newly generated user_key in the
        # session:
        if self.qualify_key('user_key') not in self.request.session:
            self.request.session[self.qualify_key('user_key')] = \
                str(random.randint(0, sys.maxint))
            session_keys = ['variant', 'via'] + self.demographic_keys.keys()
            for k in session_keys:
                self.request.session[self.qualify_key(k)] = data[k]

        # However, the Google Analytics experiment may cause a
        # subsequent reload (with user_key already set) to a different
        # variant; since we're about to use the session variables to
        # update the context, make sure the session's variant matches
        # what was requested in the URL:
        self.request.session[self.qualify_key('variant')] = variant

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

        user_key = self.request.session[self.qualify_key('user_key')]
        # Setting a seed with random.seed would not be thread-safe,
        # and potentially unsafe if randint values (say) are used for
        # anything with a security implication; instead create a
        # Random object for shuffling the partials.
        local_random = random.Random()
        local_random.seed(user_key)

        context['share_partials'] = [
            '_share_twitter.html',
            '_share_facebook.html',
        ]
        local_random.shuffle(context['share_partials'])

        context['major_partials'] = self.major_partials[:]
        local_random.shuffle(context['major_partials'])

        return context


class ExperimentRecordTimeOnPage(ExperimentViewDataMixin, View):

    http_methods_names = [u'post']

    def post(self, request, *args, **kwargs):
        def get_response(status, message=None):
            result = {'status': status}
            if message is not None:
                result['message'] = message
            return HttpResponse(
                json.dumps(result),
                content_type='application/json',
            )
        if 'seconds' not in self.request.POST:
            return get_response('error', 'No seconds parameter found')
        try:
            seconds = float(self.request.POST['seconds'])
        except ValueError:
            return get_response('error', 'Malformed seconds value')
        self.create_event({
            'category': 'time-on-page',
            'action': 'ping',
            'seconds_on_page': seconds,
        })
        return get_response('ok')


class ExperimentThanks(ExperimentViewDataMixin, TemplateView):
    """For recording voting actions which do not redirect"""

    template_name = 'vote-thanks.html'

    def get_context_data(self, **kwargs):
        context = {}
        action_value = 'click'
        category = 'form'

        # override default values if supplied
        if self.request.GET.get('val'):
            action_value = self.request.GET.get('val')
        if self.request.GET.get('cat'):
            category = self.request.GET.get('cat')

        self.create_event({'category': category,
                           'action': action_value,
                           'label': self.request.GET.get('label')})

        context['base_url'] = reverse(self.base_view_name)
        return context


class CountyPerformanceView(MITExperimentView):
    """This view displays a page about county performance with calls to action

    There are some elements of the page that are supposed to be
    randomly ordered.  There are also three major variants of the
    page that include different information."""

    template_name = 'county-performance.html'

    def get_context_data(self, **kwargs):
        context = super(CountyPerformanceView, self).get_context_data(**kwargs)

        # For convenience and readability, just assign this to a local
        # variable.
        variant = context['variant']

        context['petition_form'] = CountyPerformancePetitionForm()
        context['senate_form'] = CountyPerformanceSenateForm()

        # Add URLs based on the experiment that's being run:
        context['petition_submission_url'] = \
            reverse(self.base_view_name + '-petition-submission')
        context['senate_submission_url'] = \
            reverse(self.base_view_name + '-senate-submission')

        context['show_social_context'] = variant in ('ns', 'ts', 'os')
        context['show_threat'] = (variant[0] == 't')
        context['show_opportunity'] = (variant[0] == 'o')

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


class YouthEmploymentView(MITExperimentView):
    """This view displays a page about youth employment with calls to action

    There are some elements of the page that are supposed to be
    randomly ordered.  There are also two major variants of the
    page that include different information."""

    template_name = 'youth-employment.html'

    def get_context_data(self, **kwargs):
        context = super(YouthEmploymentView, self).get_context_data(**kwargs)

        # For convenience and readability, just assign this to a local
        # variable.
        variant = context['variant']

        # Add URLs based on the experiment that's being run:
        context['input_url'] = reverse(self.base_view_name + '-input')
        context['comment_submission_url'] = \
            reverse(self.base_view_name + '-comment-submission')
        context['support_submission_url'] = \
            reverse(self.base_view_name + '-support-submission')
        context['input_submission_url'] = \
            reverse(self.base_view_name + '-input-submission')
        context['comment_form'] = YouthEmploymentCommentForm()
        context['support_form'] = YouthEmploymentSupportForm()

        context['show_youth'] = (variant[0] == 'y')

        return context


class YouthEmploymentSupportSubmission(ExperimentFormSubmissionMixin,
                                        FormView):
    """A view for handling submitted indications of support for a bill"""

    template_name = 'youth-employment.html'
    form_class = YouthEmploymentSupportForm
    form_key = 'support'

    def get_success_url(self):
        return '/{0}/support/thanks'.format(self.base_view_name)

    def create_feedback_from_form(self, form):
        # Instead of recording this data with feedback, add it to
        # extra_data.
        pass

    def get_event_data(self, form):
        if 'submit-yes' in form.data:
            action_value = 'click-yes'
        elif 'submit-no' in form.data:
            action_value = 'click-no'
        else:
            raise Exception('Neither click-yes nor click-no found in support form data')
        return {
            'category': 'form',
            'action': action_value,
            'label': self.form_key,
            'constituency': form.cleaned_data.get('constituencies').slug,
        }


class YouthEmploymentInputSubmission(ExperimentFormSubmissionMixin, FormView):
    """A view for handling submission of whether the MP cares about the issue"""

    template_name = 'youth-employment.html'
    form_class = YouthEmploymentInputForm
    form_key = 'input'

    def get_success_url(self):
        return '/{0}/input/thanks'.format(self.base_view_name)

    def create_feedback_from_form(self, form):
        pass

    def get_event_data(self, form):
        if 'submit-yes' in form.data:
            action_value = 'click-yes'
        elif 'submit-no' in form.data:
            action_value = 'click-no'
        else:
            raise Exception('Neither click-yes nor click-no found in input form data')
        return {
            'category': 'form',
            'action': action_value,
            'label': self.form_key
        }


class YouthEmploymentCommentSubmission(ExperimentFormSubmissionMixin,
                                          FormView):
    """A view for handling submissions of comments"""

    template_name = 'youth-employment.html'
    form_class = YouthEmploymentCommentForm
    form_key = 'comment'

    def get_success_url(self):
        return '/{0}/comment/thanks'.format(self.base_view_name)

    def create_feedback_from_form(self, form):
        new_comment = form.cleaned_data.get('comments', '').strip()
        self.create_feedback(form, comment=new_comment)


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
