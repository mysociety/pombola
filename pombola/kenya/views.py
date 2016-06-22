# Create your views here.
# -*- coding: utf-8 -*-

import logging
import random
import json
import sys

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.base import View, TemplateView, RedirectView
from django.views.generic.edit import FormView

from .forms import (
    CountyPerformancePetitionForm, CountyPerformanceSenateForm,
    YouthEmploymentCommentForm, YouthEmploymentSupportForm,
    YouthEmploymentInputForm
)

from info.models import InfoPage, Tag
from pombola.core.models import Person, Place
from pombola.core.views import HomeView, PersonDetail, PersonDetailSub
from pombola.experiments.views import (
    ExperimentViewDataMixin, ExperimentFormSubmissionMixin,
    sanitize_parameter
)
from pombola.hansard.views import HansardPersonMixin
from pombola.kenya import shujaaz


logger = logging.getLogger('django.request')

EXPERIMENT_DATA = {
    'mit-county': {
        'session_key_prefix': 'MIT',
        'base_view_name': 'county-performance',
        'pageview_label': 'county-performance',
        'template_prefix': 'county',
        'experiment_key': None,
        'qualtrics_sid': 'SV_5hhE4mOfYG1eaOh',
        'variants': ('o', 't', 'n', 'os', 'ts', 'ns'),
        'default_variant': 'n',
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
        'default_variant': 'n',
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
        'default_variant': 'n',
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
    },
    'youth-employment-bill-generic-no-randomization': {
        'session_key_prefix': 'MIT4',
        'base_view_name': 'youth-employment-n',
        'pageview_label': 'youth-employment-n',
        'template_prefix': 'youth',
        'experiment_key': settings.YOUTH_EMPLOYMENT_BILL_EXPERIMENT_KEY,
        'qualtrics_sid': 'SV_ebVXgzAevcuo2sB',
        'variants': ('n',),
        'default_variant': 'n',
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
    },
}


class KEHomeView(HomeView):

    def get_context_data(self, **kwargs):
        context = super(KEHomeView, self).get_context_data(**kwargs)
        context['election_blog_posts'] = InfoPage.objects.filter(
            tags__slug='elections-2017').order_by('-publication_date')
        return context


class KEPersonDetailBase(PersonDetail):
    def get_context_data(self, **kwargs):
        context = super(KEPersonDetailBase, self).get_context_data(**kwargs)

        political_positions = self.object.position_set.all().political().currently_active()

        na_memberships = political_positions.filter(title__slug='member-national-assembly')
        na_memberships_count = na_memberships.count()
        if na_memberships_count > 1:
            logger.error(
                '{} - Too many NA memberships ({})'.format(self.object.slug, na_memberships_count))

        senate_memberships = political_positions.filter(title__slug='senator')
        senate_memberships_count = senate_memberships.count()
        if senate_memberships_count > 1:
            logger.error(
                '{} - Too many Senate memberships ({})'.format(self.object.slug, senate_memberships_count))

        if na_memberships_count:
            constituencies = Place.objects.filter(position=na_memberships[0]).distinct()
        elif senate_memberships_count:
            constituencies = Place.objects.filter(position=senate_memberships[0]).distinct()
        else:
            constituencies = []

        context['constituencies'] = constituencies

        return context

class KEPersonDetail(HansardPersonMixin, KEPersonDetailBase):
    def get_context_data(self, **kwargs):
        context = super(KEPersonDetail, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":3"

        cdf_constituencies = self.object.constituencies().filter(
            budget_entries__organisation='Constituencies Development Fund'
        ).select_related()

        # We only retrieve one budget because we only really care about the
        # latest. budgets() are default sorted by date of the budget session.
        cdf_budget_constituencies = [
            {'constituency': c, 'budget': c.budgets()[0]}
            for c in cdf_constituencies
        ]

        context['cdf_budget_constituencies'] = cdf_budget_constituencies

        context['shujaaz_finalist_info'] = [
            (
                year,
                'shujaaz-finalists-' + year,
                shujaaz.FINALISTS_DICT[year].get(self.object.pk)
            )
            for year in ('2015', '2014')
            if shujaaz.FINALISTS_DICT[year].get(self.object.pk)
        ]

        return context


class KEPersonDetailAppearances(HansardPersonMixin, PersonDetailSub, KEPersonDetailBase):
    def get_context_data(self, **kwargs):
        context = super(KEPersonDetailAppearances, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":5"
        context['lifetime_summary'] = context['hansard_entries'] \
            .monthly_appearance_counts()
        return context


class KEPersonDetailExperience(HansardPersonMixin, PersonDetailSub, KEPersonDetailBase):
    pass


class MITExperimentView(ExperimentViewDataMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super(MITExperimentView, self).get_context_data(**kwargs)

        context['experiment_key'] = self.experiment_key
        context['base_url'] = reverse(self.base_view_name)
        context['survey_url'] = reverse(self.base_view_name + '-survey')
        context['share_url'] = reverse(self.base_view_name + '-share')

        # Sanitize all the GET parameters:
        data = self.sanitize_data_parameters(
            self.request,
            self.request.GET
        )

        # If there's no user key in the session, this is the first
        # page view, so record any parameters indicating where the
        # user came from (Facebook demographics or the 'via' parameter
        # from a social share) and a newly generated user_key in the
        # session:
        if self.qualify_key('user_key') not in self.request.session:
            self.request.session[self.qualify_key('user_key')] = \
                str(random.randint(0, sys.maxint))
            session_keys = ['via'] + self.demographic_keys.keys()
            for k in session_keys:
                self.set_session_value(k, data[k])

        user_key = self.get_session_value('user_key')

        # Setting a seed with random.seed would not be thread-safe,
        # and potentially unsafe if randint values (say) are used for
        # anything with a security implication; instead create a
        # Random object for picking the variant and shuffling the
        # partials.
        local_random = random.Random()
        local_random.seed(user_key)

        variant_to_use = self.get_variant_from_session()
        if not variant_to_use:
            # Then we should pick one at random, and store it in
            # the session too:
            variant_to_use = self.get_random_variant(local_random)
            self.set_session_value('variant', variant_to_use)

        # Add those session parameters to the context for building the
        # Qualtrics survey URL, and to set the variant in the context:
        context.update(self.get_session_data())

        # Now create the page view event:
        self.create_event({
            'category': 'page',
            'action': 'view',
            'label': self.pageview_label,
        })

        # So that for testing we can see a particular variant, if
        # force-variant is set, then use that for displaying the page,
        # regardless of the variant stored in the session:
        if 'force-variant' in self.request.GET:
            sanitized_force_variant = sanitize_parameter(
                'force-variant',
                self.request.GET,
                self.variants,
                default_value=self.default_variant
            )
            context['variant'] = sanitized_force_variant

        # Now make sure the elements of the page that have to come in
        # random order are appropriately shuffled:
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
        context['bill_url'] = reverse(self.base_view_name + '-bill')
        context['input_url'] = reverse(self.base_view_name + '-input')
        context['comment_submission_url'] = \
            reverse(self.base_view_name + '-comment-submission')
        context['support_submission_url'] = \
            reverse(self.base_view_name + '-support-submission')
        context['input_submission_url'] = \
            reverse(self.base_view_name + '-input-submission')
        context['time_on_page_url'] = \
            reverse(self.base_view_name + '-time-on-page')
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


class YouthEmploymentBillView(ExperimentViewDataMixin, RedirectView):
    """A view to handle redirecting to the bill PDF"""
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        self.create_event({'category': 'read-bill',
                           'action': 'click',
                           'label': 'read-bill'})
        url = "http://info.mzalendo.com/media_root/file_archive/NATIONAL_YOUTH_EMPLOYMENT_BUREAU_BILL_2015_-_Hon._Sakaja.pdf"
        return url


class ThanksTemplateView(TemplateView):

    base_view_name = None

    def get_context_data(self, **kwargs):
        context = super(ThanksTemplateView, self).get_context_data(**kwargs)
        context['base_url'] = reverse(self.base_view_name)
        return context


class ShujaazFinalists2014View(TemplateView):
    template_name = 'shujaaz-2014.html'

    def get_context_data(self, **kwargs):
        context = super(ShujaazFinalists2014View, self).get_context_data(**kwargs)

        def populate_person(f):
            finalist = dict(f)
            finalist['person'] = Person.objects.get(pk=finalist['person'])
            return finalist

        finalists = [populate_person(f) for f in shujaaz.FINALISTS2014]
        half = len(finalists) / 2
        context['finalists_column_1'] = finalists[:half]
        context['finalists_column_2'] = finalists[half:]
        return context


class ShujaazFinalists2015View(TemplateView):
    template_name = 'shujaaz-2015.html'

    def get_context_data(self, **kwargs):
        context = super(ShujaazFinalists2015View, self).get_context_data(**kwargs)

        def populate_person(f):
            finalist = dict(f)
            finalist['person'] = Person.objects.get(pk=finalist['person'])
            return finalist

        finalists = [populate_person(f) for f in shujaaz.FINALISTS2015]
        half = len(finalists) / 2
        context['finalists_column_1'] = finalists[:half]
        context['finalists_column_2'] = finalists[half:]

        return context
