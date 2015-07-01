import json
from random import randint
import re
import sys

from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.views.generic.base import RedirectView

from pombola.experiments.models import Experiment
from pombola.feedback.models import Feedback


class ExperimentViewDataMixin(object):
    """A mixin with helper methods for creating events and feedback

    This assumes that you've created the view with as_view specifying
    keyword arguments including:

        experiment_slug (the slug for the Experiment model)
        session_key_prefix (the prefix used before keys in the session)

    Note that this mixin also assumes that you have the only keys you
    need to store in the session are those identifying the user
    ('user_key'), their demographics (e.g. 'g', 'agroup' etc.), the
    variant they got ('variant') and whether they came from a particular
    message shared on social media ('via').
    """

    # We need to set all of these on the class, since you may only
    # pass as keyword parameters into as_view properties that already
    # exist on the class.
    experiment_slug = None
    session_key_prefix = None
    base_view_name = None
    pageview_label = None
    template_prefix = None
    experiment_key = None
    qualtrics_sid = None
    variants = None
    demographic_keys = None
    major_partials = None

    def qualify_key(self, key):
        prefix = self.session_key_prefix
        return prefix + ':' + key

    def get_session_value(self, key):
        return self.request.session.get(self.qualify_key(key))

    def set_session_value(self, key, value):
        self.request.session[self.qualify_key(key)] = value

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
        session_keys = ['user_key', 'variant', 'via']
        session_keys += self.demographic_keys.keys()
        for key in session_keys:
            value = self.get_session_value(key)
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
        extra_data['user_agent'] = self.request.META.get('HTTP_USER_AGENT', '')
        extra_data_json = json.dumps(extra_data)
        event_kwargs['extra_data'] = extra_data_json
        experiment = Experiment.objects.get(slug=self.experiment_slug)
        experiment.event_set.create(**event_kwargs)

    def sanitize_data_parameters(self, request, parameters):
        """Return a cleaned version of known experiment parameters"""
        result = {}
        result['variant'] = sanitize_parameter(
            key='variant',
            parameters=parameters,
            allowed_values=self.variants,
            default_value='n')
        for key, possible_values in self.demographic_keys.items():
            result[key] = sanitize_parameter(
                key=key,
                parameters=parameters,
                allowed_values=possible_values,
                default_value='?'
            )
        result['user_key'] = sanitize_random_key('user_key', parameters)
        result['via'] = sanitize_random_key('via', parameters)
        return result


class ExperimentFormSubmissionMixin(ExperimentViewDataMixin):
    """A mixin useful for handling form data posted from an experiment page"""

    def form_invalid(self, form):
        """Redirect back to a reduced version of the page from either form"""
        extra_context = {
            '{0}_form'.format(self.form_key): form,
            'major_partials': ['_{0}_{1}.html'.format(self.template_prefix, self.form_key)],
            'correct_errors': True}
        context = self.get_context_data(**extra_context)
        return self.render_to_response(context)

    def get_event_data(self, form):
        return {
            'category': 'form',
            'action': 'submit',
            'label': self.form_key
        }

    def form_valid(self, form):
        self.create_feedback_from_form(form)
        self.create_event(self.get_event_data(form))
        return super(ExperimentFormSubmissionMixin,
                     self).form_valid(form)

class ExperimentShare(ExperimentViewDataMixin, RedirectView):
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


class ExperimentSurvey(ExperimentViewDataMixin, RedirectView):
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
            for k in ['user_key', 'variant'] + self.demographic_keys.keys()
        )
        return url


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
