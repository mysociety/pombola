import re

from django.db import models

from core.models import Person

class AliasQuerySet(models.query.QuerySet):
    def unassigned(self):
        return self.filter(person__isnull=True, ignored=False)


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
      has val  | False    | use this alias                             
      None     | True     | ignore this alias                          
      None     | False    | Human should inspect this entry            
      has val  | True     | Does not make sense - entry will be ignored

    When the check is run for missing aliases entries are made with both person
    and ignored as None for aliases that are found. These can then be used in
    the interface to find the next alias that needs to be filled in.

    """

    alias   = models.CharField( max_length=40, unique=True )
    person  = models.ForeignKey( Person, blank=True, null=True )
    ignored = models.BooleanField( default=False )
    
    objects = AliasManager()

    def __unicode__(self):
        string = self.alias
        if self.person:
            string += " (aka %s)" % self.person.name()
        return string
    
    class Meta:
        ordering = ['alias']
        app_label = 'hansard'
        verbose_name_plural = 'aliases'
