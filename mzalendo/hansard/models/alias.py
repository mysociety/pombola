import re

from django.db import models

from core.models import Person

class AliasQuerySet(models.query.QuerySet):
    pass

class AliasManager(models.Manager):
    def get_query_set(self):
        return AliasQuerySet(self.model)        

class Alias(models.Model):
    """
    Model for linking a parliamentary alias to a person
    
    The person and ignored fields can both be blank. Their combinations have
    the following meanings:
    
      person   | ignored  | meaning
      ---------+----------+--------------------------------------------
      has val  | None     | use this alias                             
      None     | has val  | ignore this alias                          
      None     | None     | Human should inspect this entry            
      has val  | has val  | Does not make sense - entry will be ignored

    When the check is run for missing aliases entries are made with both person
    and ignored as None for aliases that are found. These can then be used in
    the interface to find the next alias that needs to be filled in.

    """

    alias   = models.CharField( max_length=40, unique=True )
    person  = models.ForeignKey( Person, blank=True, null=True )
    ignored = models.BooleanField( default=False )

    def __unicode__(self):
        return "%s (aka %s)" % ( self.alias, self.person.name() )
    
    class Meta:
        ordering = ['alias']
        app_label = 'hansard'
        verbose_name_plural = 'aliases'
