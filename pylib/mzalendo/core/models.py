from django.contrib.gis.db import models
from django_date_extensions.fields import ApproximateDateField

# tell South how to handle the custom fields 
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^django_date_extensions\.fields\.ApproximateDateField"])
add_introspection_rules([], ["^django.contrib\.gis\.db\.models\.fields\.PointField"])

class Person(models.Model):
    slug            = models.SlugField(max_length=200, unique=True)
    title           = models.CharField(max_length=20)
    first_name      = models.CharField(max_length=100)
    middle_names    = models.CharField(max_length=100, blank=True)
    last_name       = models.CharField(max_length=100)
    gender          = models.CharField(max_length=1, choices=(('m','Male'),('f','Female')) )
    date_of_birth   = ApproximateDateField(blank=True)
    date_of_death   = ApproximateDateField(blank=True)
    # religion
    # tribe
    
    def get_name(self):
        return "%s %s" % ( self.first_name, self.last_name )
    
    def __unicode__(self):
        return "%s %s (%s)" % ( self.first_name, self.last_name, self.slug )

    # @models.permalink
    # def get_absolute_url(self):
    #     return ( 'core.views.person', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      
    

class Organisation(models.Model):
    slug                = models.SlugField(max_length=200, unique=True)
    name                = models.CharField(max_length=200)
    organisation_type   = models.CharField(max_length=50)
    started             = ApproximateDateField(blank=True)
    ended               = ApproximateDateField(blank=True)

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.slug )

    # @models.permalink
    # def get_absolute_url(self):
    #     return ( 'core.views.organisation', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class Place(models.Model):
    slug            = models.SlugField(max_length=100, unique=True)
    name            = models.CharField(max_length=200)
    place_type      = models.CharField(max_length=50)
    shape_url       = models.URLField(verify_exists=True, blank=True )
    location        = models.PointField(null=True, blank=True)
    organisation    = models.ForeignKey('Organisation', null=True, blank=True )

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.slug )

    # @models.permalink
    # def get_absolute_url(self):
    #     return ( 'core.views.place', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class Position(models.Model):
    person          = models.ForeignKey('Person')
    organisation    = models.ForeignKey('Organisation')
    title           = models.CharField(max_length=200)
    start_date      = ApproximateDateField(blank=True)
    end_date        = ApproximateDateField(blank=True)
    
    def __unicode__(self):
        return "%s (%s at %s)" % ( self.title, self.person.get_name(), self.organisation.name )

    class Meta:
       ordering = ["title"]      
