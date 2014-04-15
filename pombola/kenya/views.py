from random import shuffle

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import CountyPerformancePetitionForm, CountyPerformanceSenateForm

from django.shortcuts import redirect

from pombola.feedback.models import Feedback


class CountyPerformanceView(TemplateView):
    """This view displays a page about county performance with calls to action

    There are some elements of the page that are supposed to be
    randomly ordered.  There are also three major variants of the
    page that include different information."""

    template_name = 'county-performance.html'

    def get_context_data(self, **kwargs):
        context = super(CountyPerformanceView, self).get_context_data(**kwargs)
        context['suppress_banner'] = True
        context['petition_form'] = CountyPerformancePetitionForm()
        context['senate_form'] = CountyPerformanceSenateForm()

        context['show_opportunity'], context['show_threat'] = {
            'o': (True, False),
            't': (False, True),
            'n': (False, False),
            None: (False, False),
        }[self.request.GET.get('variant')]

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


class CountyPerformanceSubmissionMixin(object):
    """A mixin useful for handling senate comment and petition emails"""

    def create_feedback(self, comment='', email=''):
        """A helper method for adding feedback to the database"""
        feedback = Feedback()
        feedback.status = 'non-actionable'
        feedback.comment = comment
        feedback.email = email
        feedback.url = self.request.build_absolute_uri()
        if self.request.user.is_authenticated():
            feedback.user = self.request.user
        feedback.save()

    def form_invalid(self, form):
        """Redirect back to a reduced version of the page from either form"""
        extra_context = {
            '{0}_form'.format(self.form_key): form,
            'major_partials': ['_county_{0}.html'.format(self.form_key)],
            'suppress_banner': True,
            'correct_errors': True}
        context = self.get_context_data(**extra_context)
        return self.render_to_response(context)


class CountyPerformanceSenateSubmission(CountyPerformanceSubmissionMixin,
                                        FormView):
    """A view for handling submissions of comments for the senate"""

    template_name = 'county-performance.html'
    success_url = '/county-performance/senate/thanks'
    form_class = CountyPerformanceSenateForm
    form_key = 'senate'

    def form_valid(self, form):
        new_comment = u"senate feedback: "
        new_comment += form.cleaned_data.get('comments', '').strip()
        self.create_feedback(comment=new_comment)
        return super(CountyPerformanceSenateSubmission,
                     self).form_valid(form)


class CountyPerformancePetitionSubmission(CountyPerformanceSubmissionMixin,
                                          FormView):
    """A view for handling a petition signature"""

    template_name = 'county-performance.html'
    success_url = '/county-performance/petition/thanks'
    form_class = CountyPerformancePetitionForm
    form_key = 'petition'

    def form_valid(self, form):
        new_comment = u"petition signature from: "
        new_comment += form.cleaned_data.get('name', '').strip()
        self.create_feedback(comment=new_comment,
                             email=form.cleaned_data.get('email'))
        return super(CountyPerformancePetitionSubmission,
                     self).form_valid(form)
