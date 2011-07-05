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
    middle_names    = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    gender          = models.CharField(max_length=1, choices=(('m','Male'),('f','Female')) )
    date_of_birth   = ApproximateDateField()
    date_of_death   = ApproximateDateField()
    # religion
    # tribe

class Organisation(models.Model):
    slug                = models.SlugField(max_length=200, unique=True)
    name                = models.CharField(max_length=200)
    organisation_type   = models.CharField(max_length=50)
    started             = ApproximateDateField()
    ended               = ApproximateDateField()

class Place(models.Model):
    slug            = models.SlugField(max_length=100, unique=True)
    name            = models.CharField(max_length=200)
    place_type      = models.CharField(max_length=50)
    shape_url       = models.URLField(verify_exists=True, blank=True )
    location        = models.PointField(null=True)
    organisation    = models.ForeignKey('Organisation', null=True)
