from django.db import models


class Configuration(models.Model):
    url = models.CharField(max_length=200, help_text="URL for the WriteInPublic API without instance subdomain, e.g. http://writeinpublic.pa.org.za")
    instance_id = models.PositiveIntegerField(help_text="Instance ID, can be found at /en/manage/settings/api/ on your instance subdomain")
    # Same max_length as Django's User model, to match write-it
    username = models.CharField(max_length=30, help_text="Username for the WriteInPublic instance you want to use")
    # Same max_length as tastypie, to match write-it
    api_key = models.CharField(max_length=128, help_text="API key for the WriteInPublic instance you want to use")
    slug = models.CharField(max_length=30, unique=True, help_text="A unique human-friendly identifier for this configuration")
    person_uuid_prefix = models.CharField(max_length=200, help_text="The prefix for people's UUID")
