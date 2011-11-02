from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

from south.signals import ran_migration

class UserProfileManager(models.Manager):
    def create_missing(self):
        """Create profiles for all the users that do not have one"""
        all_user_ids_with_profiles = UserProfile.objects.values_list('id', flat=True)
        users_missing_profiles = User.objects.exclude(id__in=all_user_ids_with_profiles)

        for user in users_missing_profiles:
            UserProfile.objects.create(user=user)


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

    objects = UserProfileManager()


# make sure that profiles are created for all new users
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
post_save.connect(create_user_profile, sender=User)

# make sure that profiles are created for all new users
def check_all_user_profiles(app, migration, method, **kwargs):
    if str(migration) == 'user_profile:0002_add_userprofile' and method == 'forwards':
        UserProfile.objects.create_missing()
ran_migration.connect(check_all_user_profiles)
