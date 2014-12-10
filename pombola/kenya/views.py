# Create your views here.
# -*- coding: utf-8 -*-

import hashlib
import json
from random import randint, shuffle
import re
import sys

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView

from .forms import CountyPerformancePetitionForm, CountyPerformanceSenateForm

from django.shortcuts import redirect

from pombola.core.models import Person
from pombola.core.views import PersonDetail, PersonDetailSub
from pombola.experiments.models import Experiment, Event
from pombola.feedback.models import Feedback
from pombola.hansard.views import HansardPersonMixin

EXPERIMENT_DATA = {
    'mit-county': {
        'session_key_prefix': 'MIT',
        'base_view_name': 'county-performance',
        'pageview_label': 'county-performance',
        'experiment_key': None,
        'qualtrics_sid': 'SV_5hhE4mOfYG1eaOh',
    },
    'mit-county-larger': {
        'session_key_prefix': 'MIT2',
        'base_view_name': 'county-performance-2',
        'pageview_label': 'county-performance-2',
        'experiment_key': settings.COUNTY_PERFORMANCE_EXPERIMENT_KEY,
        'qualtrics_sid': 'SV_5hhE4mOfYG1eaOh',
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

        return context


class KEPersonDetailAppearances(HansardPersonMixin, PersonDetailSub):

    def get_context_data(self, **kwargs):
        context = super(KEPersonDetailAppearances, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":5"
        context['lifetime_summary'] = context['hansard_entries'] \
            .monthly_appearance_counts()
        return context


def sanitize_parameter(key, parameters, allowed_values, default_value=None):
    """Check that the value for key in parameters is in allowed_values

    If it's an allowed value, return that.  If it's not an allowed
    value, and there's a default_value supplied, return the
    default_value.  Otherwise (an unknown key, and no default_value)
    raise a ValueError."""
    value = parameters.get(key)
    if value not in allowed_values:
        if default_value is None:
            message = "An allowed value for '{0}' must be provided"
            raise ValueError(message.format(key))
        value = default_value
    return value

# A regular expression that the random keys we generate must match in
# order to be valid:
random_key_re = re.compile(r'^[a-zA-Z0-9]+$')

def sanitize_random_key(key, parameters):
    """Return parameters[key] if it's valid or '?' otherwise"""
    if key in parameters and random_key_re.search(parameters[key]):
        return parameters[key]
    return '?'

def sanitize_data_parameters(request, parameters):
    """Return a cleaned version of known experiment parameters"""
    result = {}
    result['variant'] = sanitize_parameter(
        key='variant',
        parameters=parameters,
        allowed_values=('o', 't', 'n', 'os', 'ts', 'ns'),
        default_value='n')
    result['g'] = sanitize_parameter(
        key='g',
        parameters=parameters,
        allowed_values=('m', 'f'),
        default_value='?')
    result['agroup'] = sanitize_parameter(
        key='agroup',
        parameters=parameters,
        allowed_values=('under', 'over'),
        default_value='?')
    result['user_key'] = sanitize_random_key('user_key', parameters)
    result['via'] = sanitize_random_key('via', parameters)
    return result


class CountyPerformanceDataMixin(object):
    """A mixin with helper methods for creating events and feedback"""

    def qualify_key(self, key):
        prefix = EXPERIMENT_DATA[self.experiment_slug]['session_key_prefix']
        return prefix + ':' + key

    def create_feedback(self, form, comment='', email=''):
        """A helper method for adding feedback to the database"""
        feedback = Feedback()
        feedback.status = 'non-actionable'
        prefix_data = self.get_session_data()
        prefix_data['experiment_slug'] = self.experiment_slug
        comment_prefix = json.dumps(prefix_data)
        feedback.comment = comment_prefix + ' ' + comment
        feedback.email = email
        feedback.url = self.request.build_absolute_uri()
        if self.request.user.is_authenticated():
            feedback.user = self.request.user
        feedback.save()

    def get_session_data(self):
        result = {}
        for key in ('user_key', 'variant', 'g', 'agroup', 'via'):
            full_key = self.qualify_key(key)
            value = self.request.session.get(full_key)
            if value is not None:
                result[key] = value
        return result

    def create_event(self, data):
        data.update(self.get_session_data())
        standard_cols = ('user_key', 'variant', 'category', 'action', 'label')
        event_kwargs = {}
        extra_data = data.copy()
        for column in standard_cols:
            if column in data:
                value = data.get(column, '?')
                if value != '?':
                    event_kwargs[column] = value
                del extra_data[column]
        extra_data_json = json.dumps(extra_data)
        event_kwargs['extra_data'] = extra_data_json
        experiment = Experiment.objects.get(slug=self.experiment_slug)
        experiment.event_set.create(**event_kwargs)


class CountyPerformanceView(CountyPerformanceDataMixin, TemplateView):
    """This view displays a page about county performance with calls to action

    There are some elements of the page that are supposed to be
    randomly ordered.  There are also three major variants of the
    page that include different information."""

    template_name = 'county-performance.html'
    experiment_slug = None

    def get_context_data(self, **kwargs):
        context = super(CountyPerformanceView, self).get_context_data(**kwargs)
        context['petition_form'] = CountyPerformancePetitionForm()
        context['senate_form'] = CountyPerformanceSenateForm()

        # Add URLs based on the experiment that's being run:
        experiment_data = EXPERIMENT_DATA[self.experiment_slug]
        base_view_name = experiment_data['base_view_name']
        context['survey_url'] = reverse(base_view_name + '-survey')
        context['base_url'] = reverse(base_view_name)
        context['share_url'] = reverse(base_view_name + '-share')
        context['petition_submission_url'] = \
            reverse(base_view_name + '-petition-submission')
        context['senate_submission_url'] = \
            reverse(base_view_name + '-senate-submission')
        context['experiment_key'] = experiment_data['experiment_key']

        data = sanitize_data_parameters(self.request, self.request.GET)
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
            label = EXPERIMENT_DATA[self.experiment_slug]['pageview_label']
            self.create_event({'category': 'page',
                               'action': 'view',
                               'label': label})

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


class CountyPerformanceSubmissionMixin(CountyPerformanceDataMixin):
    """A mixin useful for handling senate comment and petition emails"""

    def form_invalid(self, form):
        """Redirect back to a reduced version of the page from either form"""
        extra_context = {
            '{0}_form'.format(self.form_key): form,
            'major_partials': ['_county_{0}.html'.format(self.form_key)],
            'correct_errors': True}
        context = self.get_context_data(**extra_context)
        return self.render_to_response(context)

    def form_valid(self, form):
        self.create_feedback_from_form(form)
        self.create_event({'category': 'form',
                           'action': 'submit',
                           'label': self.form_key})
        return super(CountyPerformanceSubmissionMixin,
                     self).form_valid(form)


class CountyPerformanceSenateSubmission(CountyPerformanceSubmissionMixin,
                                        FormView):
    """A view for handling submissions of comments for the senate"""

    template_name = 'county-performance.html'
    form_class = CountyPerformanceSenateForm
    form_key = 'senate'
    experiment_slug = None

    def get_success_url(self):
        base_view_name = EXPERIMENT_DATA[self.experiment_slug]['base_view_name']
        return '/{0}/senate/thanks'.format(base_view_name)

    def create_feedback_from_form(self, form):
        new_comment = form.cleaned_data.get('comments', '').strip()
        self.create_feedback(form, comment=new_comment)


class CountyPerformancePetitionSubmission(CountyPerformanceSubmissionMixin,
                                          FormView):
    """A view for handling a petition signature"""

    template_name = 'county-performance.html'
    form_class = CountyPerformancePetitionForm
    form_key = 'petition'
    experiment_slug = None

    def get_success_url(self):
        base_view_name = EXPERIMENT_DATA[self.experiment_slug]['base_view_name']
        return '/{0}/petition/thanks'.format(base_view_name)

    def create_feedback_from_form(self, form):
        new_comment = form.cleaned_data.get('name', '').strip()
        self.create_feedback(form,
                             comment=new_comment,
                             email=form.cleaned_data.get('email'))


class CountyPerformanceShare(CountyPerformanceDataMixin, RedirectView):
    """For recording & enacting Facebook / Twitter share actions"""

    permanent = False
    experiment_slug = None

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
        path = reverse(EXPERIMENT_DATA[self.experiment_slug]['base_view_name'])
        built = self.request.build_absolute_uri(path)
        built += '?via=' + share_key
        url_parameter = urlquote(built, safe='')
        url_formats = {
            'facebook': "https://www.facebook.com/sharer/sharer.php?u={0}",
            'twitter': "http://twitter.com/share?url={0}"}
        return url_formats[social_network].format(url_parameter)


class CountyPerformanceSurvey(CountyPerformanceDataMixin, RedirectView):
    """For redirecting to the Qualtrics survey"""

    permanent = False
    experiment_slug = None

    def get_redirect_url(self, *args, **kwargs):
        self.create_event({'category': 'take-survey',
                           'action': 'click',
                           'label': 'take-survey'})
        prefix = EXPERIMENT_DATA[self.experiment_slug]['session_key_prefix']
        sid = EXPERIMENT_DATA[self.experiment_slug]['qualtrics_sid']
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
        finalists = [
            {
                'category': 'Education (National Assembly)',
                'name': 'Hon. Boniface Gatobu',
                'person': Person.objects.get(pk=1322),
                'reasons': '''<ul><li>Motion urging the Government, to
establish a public databank of all bright and poor students to be in the
custody of the County Director of Education, and such information
be disseminated and made available to the public institutions
including the respective Constituencies Development Fund
Committees which shall take into consideration when disbursing
bursaries and such other institutions that may be willing to
support such students.  Proposed on 15th May, 2013 and adopted in
July 2013</li></ul>''',
            },
            {
                'category': 'Education (Senate)',
                'name': 'Sen. Boni Khalwale',
                'person': Person.objects.get(pk=170),
                'reasons': '''<ul><li>Motion on equitable distribution of
universities across counties. Notice mooted on 30th April 2013 and adopted
later in May, 2013</li></ul>''',
            },
            {
                'category': 'Water',
                'name': 'Hon. Amina Abdalla',
                'person': Person.objects.get(pk=382),
                'reasons': '''<ul><li>Contributions to the Water Bill 2014 on
the importance of the separation of responsibilities between the
water authorities at the national and county government levels.
(<a href="http://info.mzalendo.com/hansard/sitting/national_assembly/2014-10-23-14-30-00#entry-494909">Read
the debate on the moving of the Water Bill</a>.)</li></ul>''',
            },
            {
                'category': 'Food',
                'name': 'Sen. Beatrice Elachi',
                'person': Person.objects.get(pk=13115),
                'reasons': '<ul><li>The Food Security Bill.</li></ul>',
            },
            {
                'category': 'Health (Senate)',
                'name': 'Sen. Dr. Wilfred Machage',
                'person': Person.objects.get(pk=179),
                'reasons': '''<ul><li>Motion urging government to establish
level 5 hospitals in all 47 counties. Motion proposed on May 23rd and adopted
in June, 2013.</li></ul>''',
            },
            {
                'category': 'Health (National Assembly)',
                'name': 'Hon. James Nyikal',
                'person': Person.objects.get(pk=434),
                'reasons': '''<ul><li>Contributions on the health sector and
devolution: “Hon. Speaker, thank you. It is true that we have a big problem
of health in the country now, which has been made worse by the
process of devolution. What I have said here many times is that
we failed to devolve the way we planned in the Constitution. The
TA and the appropriate law have never been applied. One day the
governors, the Council of Governors and the President decided to
devolve healthcare in a day. It is not possible. The problem we
are seeing in healthcare is also in other places, only that in
health area players are noisy.”
(<a href="http://info.mzalendo.com/hansard/sitting/national_assembly/2014-08-20-14-30-00#entry-486463">See
the full speech and debate.</a>)</li></ul>''',
            },
            {
                'category': 'Youth',
                'name': 'Hon. Chris Wamalwa',
                'person': Person.objects.get(pk=1889),
                'reasons': '''<ul><li>The mode of disbursement of Kshs. 6
billion initially earmarked for a Presidential runoff, to be disbursed
to the youths and women groups across the Country. Sought on 17th, July
2013, Nairobi.</li></ul>''',
            },
            {
                'category': 'Budgetary oversight',
                'name': 'Hon. John Mbadi',
                'person': Person.objects.get(pk=110),
                'reasons': '''<ul><li>The salaries, allowances, and vehicles
allocated to constitutional commissioners. Sought on 4th June,
2013.</li></ul>''',
            },
            {
                'category': 'Oversight (progressive legislation)',
                'name': 'Hon. Kabando wa Kabando',
                'person': Person.objects.get(pk=31),
                'reasons': '''<ul><li>Proposed the reintroduction of Capital
gains tax that was included in the Finance Bill 2014</li><li>Central Bank
(amendment) Act, 2014</li><li>Followed up on the Status of the Kroll report
and capital gains flight</li></ul>''',
            },
            {
                'category': 'Devolution',
                'name': 'Sen. Kithure Kindiki',
                'person': Person.objects.get(pk=1046),
                'reasons': '''<ul><li>The County Allocation of Revenue Bill,
2013; The Community Land Bill; Division of Revenue Bill, 2014 (Sen. Bill No.12)
2013; County Allocation of Revenue Bill, 2014 (Sen. Bill No.13); Public Finance
Management (Amendment) Bill, 2014 (Sen. Bill No. 11); County Assembly Powers
and Privileges Bill, 2014 (Sen. Bill No. 14); Parliamentary Powers and
Privileges Bill, 2014 (Sen. Bill No. 15); The County Retirement Scheme
Bill;</li><li>Motion urging the national government to enter into
agreements with county government to transfer resources,
functions and powers to county governments.</li></ul>''',
            },
        ]
        half = len(finalists) / 2
        context['finalists_column_1'] = finalists[:half]
        context['finalists_column_2'] = finalists[half:]
        return context
