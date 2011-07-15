import datetime
import re

from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django_date_extensions.fields import ApproximateDateField, ApproximateDate

# tell South how to handle the custom fields 
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^django_date_extensions\.fields\.ApproximateDateField"])
add_introspection_rules([], ["^django.contrib\.gis\.db\.models\.fields\.PointField"])

date_help_text = "Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'"


class ContactKind(models.Model):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]      


class Contact(models.Model):

    kind    = models.ForeignKey('ContactKind')
    value   = models.TextField()
    note    = models.TextField(blank=True, help_text="publicaly visible, use to clarify contact detail")
    source  = models.CharField(max_length=500, blank=True, default='', help_text="where did this contact detail come from")

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    def __unicode__(self):
        return "%s (%s for %s)" % ( self.value, self.kind, self.content_object )

    class Meta:
       ordering = ["content_type", "object_id", "kind", ]      


class InformationSource(models.Model):
    source  = models.CharField(max_length=500)
    note    = models.TextField(blank=True)
    entered = models.BooleanField(default=False, help_text="has the information in this source been entered into this system?")

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    def __unicode__(self):
        return "%s: %s" % ( self.source, self.content_object )

    class Meta:
       ordering = ["content_type", "object_id", "source", ]      


class PersonQuerySet(models.query.GeoQuerySet):
    def name_matches( self, name ):
        """fuzzy match on the name"""

        m = re.match('^\s*(\w+).*?(\w+)\s*$', name)
        
        if not m:
            return self.none()

        (first, last) = m.groups()
        
        return self.filter(
            first_name__istartswith=first,
            last_name__istartswith=last,
        )



    def is_mp(self):
        mp_title = PositionTitle.objects.get(slug='mp')
        return self.filter( position__title=mp_title )

class PersonManager(models.GeoManager):
    def get_query_set(self):
        return PersonQuerySet(self.model)

class Person(models.Model):
    first_name      = models.CharField(max_length=100)
    middle_names    = models.CharField(max_length=100, blank=True)
    last_name       = models.CharField(max_length=100)
    slug            = models.SlugField(max_length=200, unique=True, help_text="auto-created from first name and last name")
    gender          = models.CharField(max_length=1, choices=(('m','Male'),('f','Female')) )
    date_of_birth   = ApproximateDateField(blank=True, help_text=date_help_text)
    date_of_death   = ApproximateDateField(blank=True, help_text=date_help_text)
    original_id     = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to members in original mzalendo.com db')
    # religion
    # tribe

    contacts = generic.GenericRelation(Contact)
    objects  = PersonManager()
    
    def name(self):
        return "%s %s" % ( self.first_name, self.last_name )
    
    def __unicode__(self):
        return "%s %s (%s)" % ( self.first_name, self.last_name, self.slug )

    @models.permalink
    def get_absolute_url(self):
        return ( 'person', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class OrganisationKind(models.Model):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]      


class Organisation(models.Model):
    name    = models.CharField(max_length=200)
    slug    = models.SlugField(max_length=200, unique=True, help_text="created from name")
    kind    = models.ForeignKey('OrganisationKind')
    started = ApproximateDateField(blank=True, help_text=date_help_text)
    ended   = ApproximateDateField(blank=True, help_text=date_help_text)
    original_id = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to parties in original mzalendo.com db')

    contacts = generic.GenericRelation(Contact)

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.kind )

    @models.permalink
    def get_absolute_url(self):
        return ( 'organisation', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class PlaceKind(models.Model):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]      


class Place(models.Model):
    name         = models.CharField(max_length=200)
    slug         = models.SlugField(max_length=100, unique=True, help_text="created from name")
    kind         = models.ForeignKey('PlaceKind')
    shape_url    = models.URLField(verify_exists=True, blank=True )
    location     = models.PointField(null=True, blank=True)
    organisation = models.ForeignKey('Organisation', null=True, blank=True, help_text="use if the place uniquely belongs to an organisation - eg a field office" )
    original_id  = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to constituencies in original mzalendo.com db')

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.kind )

    @models.permalink
    def get_absolute_url(self):
        return ( 'place', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class PositionTitle(models.Model):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = models.TextField(blank=True)
    original_id     = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to data in original mzalendo.com db')

    def __unicode__(self):
        return self.name
    
    class Meta:
       ordering = ["slug"]      
    
    
class Position(models.Model):
    person          = models.ForeignKey('Person')
    organisation    = models.ForeignKey('Organisation')
    place           = models.ForeignKey('Place', null=True, blank=True, help_text="use if needed to identify the position - eg add constituency for an 'MP'" )
    title           = models.ForeignKey('PositionTitle')
    start_date      = ApproximateDateField(blank=True, help_text=date_help_text)
    end_date        = ApproximateDateField(blank=True, help_text=date_help_text)
    
    def display_start_date(self):
        """Return text that represents the start date"""
        if self.start_date:
            return str(self.start_date)
        return '???'
    
    def display_end_date(self):
        """Return text that represents the end date"""
        if self.end_date:
            return str(self.end_date)
        return '???'

    def is_ongoing(self):
        """Return True or False for whether the position is currently ongoing"""
        if not self.end_date:
            return True
        elif self.end_date.future:
            return True
        else:
            # turn today's date into an ApproximateDate object and cmp to that
            now = datetime.date.today()
            now_approx = ApproximateDate(year=now.year, month=now.month, day=now.day )
            return now_approx <= self.end_date
    
    def __unicode__(self):
        return "%s (%s at %s)" % ( self.title, self.person.name(), self.organisation.name )
