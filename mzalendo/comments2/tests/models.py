from django.conf import settings

from django.db import models


class RockStar(models.Model):
    """
    A rockstar - but just for testing!
    """

    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)

    class Meta:
        app_label = 'comments2'

    def __unicode__(self):
        return self.name