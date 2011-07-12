import datetime

from django.contrib.gis.db import models
from django_date_extensions.fields import ApproximateDateField, ApproximateDate

# tell South how to handle the custom fields 
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^django_date_extensions\.fields\.ApproximateDateField"])
add_introspection_rules([], ["^django.contrib\.gis\.db\.models\.fields\.PointField"])

date_help_text = "Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'"

class Person(models.Model):
    first_name      = models.CharField(max_length=100)
    middle_names    = models.CharField(max_length=100, blank=True)
    last_name       = models.CharField(max_length=100)
    slug            = models.SlugField(max_length=200, unique=True, help_text="auto-created from first name and last name")
    gender          = models.CharField(max_length=1, choices=(('m','Male'),('f','Female')) )
    date_of_birth   = ApproximateDateField(blank=True, help_text=date_help_text)
    date_of_death   = ApproximateDateField(blank=True, help_text=date_help_text)
    # religion
    # tribe
    
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
    summary         = models.TextField()

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
    summary         = models.TextField()

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
    summary         = models.TextField()
    
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
