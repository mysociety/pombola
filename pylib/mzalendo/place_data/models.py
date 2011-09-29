import datetime

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

from core.models import Place


class DataCategory(models.Model):
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now(), )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now(), )    

    slug        = models.SlugField( unique=True )
    name        = models.CharField( max_length=200, unique=True )
    synopsis    = models.CharField( max_length=200 )
    description = models.TextField()
    
    value_type  = models.CharField(
        max_length = 20,
        choices = (
            # A percentage, will be displayed as such.
            ('percentage', 'Percentage'),

            # Any financial value - will be formatted as the default currency
            # (handling multiple currencies currently not supported).
            ('monetary',   'Monetary amount'),

            # This is a value that goes up and down - like a temperature or a
            # population count.
            ('gauge',      'Gauge amount'),

            # Included in case it is needed in the future. A counter is expected
            # to increase so it's value is really only relevant when compared to
            # the previous value. It would need to be displayed slightly
            # differently on the site.
            # Eg an odometer in a car, a total visitors counter on a website
            # ('counter',    'Counter'), # not used 
        ),
    )
    
    class Meta():
        ordering = ( 'name', )
        verbose_name_plural = 'data categories'


class Data(models.Model):
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now(), )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now(), )    

    place    = models.ForeignKey(Place)
    category = models.ForeignKey(DataCategory)

    # Used to select the most recent data of this category. Require a full data
    # for simplicity.
    date     = models.DateField()

    # place, category, date are unique so can be used to update/overwrite
    # information when doing a CSV upload - see unique_together in Meta below.

    value    = models.FloatField() 

    general_remark      = models.CharField( max_length= 400 )              # An unacceptable amount of money is missing or unaccounted for in this constituency. 
    comparative_remark  = models.CharField( max_length= 400 )              # This is an above average performance
    equivalent_remark   = models.CharField( max_length= 400, blank=True )  # Enough money is going missing to pay for 123 teachers
    
    # Every data point should have an external source. 
    source_url  = models.URLField()  
    source_name = models.CharField( max_length=200 )

    class Meta():
        ordering = ( '-date', 'category', 'place' )
        unique_together = ( 'place', 'category', 'date' )
        verbose_name_plural = 'data'
