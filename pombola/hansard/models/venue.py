from django.db import models

from pombola.hansard.models.base import HansardModelBase

class Venue(HansardModelBase):
    """
    Venues for the sittings
    """

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        app_label = 'hansard'
        ordering = [ 'slug' ]

    def __unicode__(self):
        return self.name
