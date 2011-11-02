from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)

    # should we create a public profile page for this user?
    is_profile_public = models.NullBooleanField()

    # private details
    mobile = models.CharField(max_length=30, blank=True)

    # other web presence
    facebook = models.CharField(max_length=30, blank=True)
    twitter  = models.CharField(max_length=30, blank=True)

    # location
    constituency = models.ForeignKey(
        'core.Place',
        limit_choices_to = {
            'kind__slug': 'constituency',
        },
        blank=True, null=True,
    )
