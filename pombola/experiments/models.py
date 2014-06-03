import json

from django.db import models

class Experiment(models.Model):
    """A model to represent a particular experiment, e.g. an A/B test"""
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    @property
    def extra_fields(self):
        result = set()
        for event in self.event_set.all():
            result.update(json.loads(event.extra_data).keys())
        return result

class Event(models.Model):
    """A model to represent an event as part of an experiment, e.g. a button click"""
    experiment = models.ForeignKey('Experiment')
    user_key = models.CharField(
        max_length=512,
        help_text='An identifier for a user, e.g. based on the session key')
    variant = models.CharField(
        max_length=128,
        help_text='This identifies the page variant presented to the user')
    category = models.CharField(
        max_length=128,
        help_text='Following GA, "Typically the object that was interacted with (e.g. button)"')
    action = models.CharField(
        max_length=128,
        help_text='Following GA, "The type of interaction (e.g. click)"')
    label = models.CharField(
        max_length=128,
        help_text='Following GA, "Useful for categorizing events (e.g. nav buttons)"')
    extra_data = models.TextField(
        blank=True,
        help_text='For arbitrary additional data, which should be valid JSON or empty')
    created = models.DateTimeField(auto_now_add=True)
