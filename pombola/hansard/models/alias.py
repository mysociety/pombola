import re
import datetime

from django.db import models

from pombola.hansard.models.base import HansardModelBase
from pombola.core.models import Person

class AliasQuerySet(models.query.QuerySet):
    def unassigned(self):
        """
        Limit to aliases that have not been assigned.
        """
        return self.filter(person__isnull=True, ignored=False)


class AliasManager(models.Manager):
    def get_query_set(self):
        return AliasQuerySet(self.model)


class Alias(HansardModelBase):
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

    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now, )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now, )

    alias   = models.CharField( max_length=200, unique=True )
    person  = models.ForeignKey(
        Person, blank=True, null=True, limit_choices_to={'hidden': False}
    )
    ignored = models.BooleanField( default=False )
    
    objects = AliasManager()

    def __unicode__(self):
        string = self.alias
        if self.person:
            string += " (aka %s)" % self.person.name
        return string
    
    class Meta:
        ordering = ['alias']
        app_label = 'hansard'
        verbose_name_plural = 'aliases'
    
    def is_unassigned(self):
        return bool(not self.person and not self.ignored)

    @classmethod
    def clean_up_name(cls, name):
        name = name.strip()
        name = re.sub( r'\s+',                    r' ',    name )
        name = re.sub( r'^Sen\.\s+\((.*?)\)',     r'\1',   name )
        name = re.sub( r'^\(\s*(.*)\s*\)$',       r'\1',   name )
        name = re.sub( r'^\[\s*(.*)\s*\]$',       r'\1',   name )
        name = re.sub( r'\s*,+$',                 r'',     name )
        name = re.sub( r'\.(\S)',                 r'. \1', name )

        # Take titles and add a '.' after if needed
        name = re.sub( r'^(Mr|Mrs|Ms|Prof|Eng|Dr) ', r'\1. ',  name )
        

        return name
    
    @classmethod
    def can_ignore_name(cls, name):
    
        # Ignore anything with numbers in
        if re.search(r'\d', name):
            return True
    
        # Ignore titles - they start with 'The'
        if re.match(r'The', name):
            return True
    
        # Ignore anything with CAPITALS in
        if re.search(r'[A-Z]{3,}', name):
            return True
    
        # Ignore anything with Speaker in it
        if re.search(r'\bSpeaker\b', name):
            return True
    
        # Ignore anything that looks like a bullet point
        if re.match(r'\(.\)', name) or re.match(r'\(i{0,3}v?i{0,3}\)', name):
            return True
    
        # Ignore anything that looks like an parliamentary support role
        if re.search( r'\bTellers\b', name):
            return True
    
        return False
    
