# This is a lightly modified version of the function from
# social_auth.backends.pipeline.user but with the tweak that the details are
# only set when the user is created and then not changed on subsequent logins.
# There is a fair bit of magic left behind here though so it is possible that
# the packaged function will change making this one broken.
#
# The exact function that was copied (as well as the imports) is available here:
#   https://github.com/omab/django-social-auth/blob/79815a77359a21a4eb23e5c8a1a72ba5b2430666/social_auth/backends/pipeline/user.py


from uuid import uuid4

from django.conf import settings

from social_auth.models import User
from social_auth.backends.pipeline import USERNAME, USERNAME_MAX_LENGTH, warn_setting
from social_auth.signals import socialauth_not_registered, \
                                socialauth_registered, \
                                pre_update


def update_user_details(backend, details, response, user, is_new=False, *args, **kwargs):
    """Update user details using data from provider."""

    # we don't want to change anything unless the user is new
    if not is_new:
        return

    changed = False  # flag to track changes

    for name, value in details.iteritems():
        # do not update username, it was already generated
        if name == USERNAME:
            continue
        if value and value != getattr(user, name, None):
            setattr(user, name, value)
            changed = True

    # Fire a pre-update signal sending current backend instance,
    # user instance (created or retrieved from database), service
    # response and processed details.
    #
    # Also fire socialauth_registered signal for newly registered
    # users.
    #
    # Signal handlers must return True or False to signal instance
    # changes. Send method returns a list of tuples with receiver
    # and it's response.
    signal_response = lambda (receiver, response): response
    signal_kwargs = {'sender': backend.__class__, 'user': user,
                     'response': response, 'details': details}

    changed |= any(filter(signal_response, pre_update.send(**signal_kwargs)))

    # Fire socialauth_registered signal on new user registration
    if is_new:
        changed |= any(filter(signal_response,
                              socialauth_registered.send(**signal_kwargs)))

    if changed:
        user.save()
