import re

from django.db import models

from core.models import Person

class Alias(models.Model):
    """Model for linking a parliamentary alias to a person"""

    alias   = models.CharField( max_length=40, unique=True )
    person  = models.ForeignKey( Person, blank=True, null=True )
    ignored = models.BooleanField( default=False )

    def __unicode__(self):
        return "%s (aka %s)" % ( self.alias, self.person.name() )
    
    class Meta:
        ordering = ['alias']
        app_label = 'hansard'
        verbose_name_plural = 'aliases'
