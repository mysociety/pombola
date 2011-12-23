import time
import datetime

from django import forms
from django.forms.util import ErrorDict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import salted_hmac, constant_time_compare
from django.utils.encoding import force_unicode
from django.utils.hashcompat import sha_constructor
from django.utils.text import get_text_list
from django.utils.translation import ungettext, ugettext_lazy as _

from feedback.models import Feedback

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
    )
