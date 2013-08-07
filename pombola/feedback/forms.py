import time
import datetime

from django import forms
from django.forms.util import ErrorDict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import salted_hmac, constant_time_compare
from django.utils.encoding import force_unicode
from django.utils.text import get_text_list
from django.utils.translation import ungettext, ugettext_lazy as _

from pombola.feedback.models import Feedback

class FeedbackForm(forms.Form):
    """
    Gather feedback
    """

    url = forms.URLField(
        widget   = forms.HiddenInput,
        required = False,
    )

    comment = forms.CharField(
        label  = _('Your feedback'),
        widget = forms.Textarea,
        max_length = 2000,
    )

    email = forms.EmailField(
        label  = _('Your email'),
        required = False,
        help_text = "optional - but lets us get back to you...",
    )

    # This is a honeypot field to catch spam bots. If there is any content in
    # it the feedback status will be set to 'spammy'. This field is hidden by
    # CSS in the form so should never be shown to a user. Hopefully it will not
    # be autofilled either.
    website = forms.CharField(
        label = _('Leave this blank'),
        required = False,
    )
    
