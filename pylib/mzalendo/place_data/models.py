import datetime
import dateutil.parser
import csv

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError, ObjectDoesNotExist

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
    
    def __unicode__(self):
        return self.name
    
    
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

    def __unicode__(self):
        return '%s for %s (%s)' % (self.category, self.place, self.date)

    @classmethod
    def process_csv(cls, csv_file, save=False):
        """
        Take a CSV file and process the entries. Returns a results hash with
        errors and data objects. If 'save' is True the database is updated.
        """
        reader = csv.DictReader( csv_file )

        entries     = []
        duplicate_catcher = {} # key is category_id-place_id-date, val is line number

        # check that the headers are what we expect

        expected_headers = set(['place_slug', 'category_slug', 'date', 'value',
        'general_remark', 'comparative_remark', 'equivalent_remark',
        'source_url', 'source_name'])
        actual_headers = set( reader.fieldnames )
        if actual_headers != expected_headers:
            # try to produce a friendly error
            missing = expected_headers - actual_headers
            extra   = actual_headers - expected_headers
            if missing:
                file_error = 'Missing expected header(s): %s' % ', '.join(missing)
            else:
                file_error = 'Found unexpected header(s): %s' % ', '.join(extra)
            return { "file_error": file_error }

        for row in reader:
            entry = dict(
                line_number = reader.line_num,
                error       = None,
                action      = None,
            )
            entries.append( entry )

            # Extract the values that need to be inflated
            try:
                place    = Place.objects.get( slug=row['place_slug'] )
                category = DataCategory.objects.get( slug=row['category_slug'] )
                date = dateutil.parser.parse( row['date'] ).date()
            except ValueError:
                entry['error'] = "date: Not a valid yyyy/mm/dd date: '%s'" % row['date']
                continue
            except ObjectDoesNotExist:
                entry['error'] = "place or category slug not found"
                continue

            # check that we've not seen this entry before in this file
            duplicate_catcher_key = '-'.join([ str(place.id), str(category.id), str(date) ])
            line_num = duplicate_catcher.get(duplicate_catcher_key)
            if line_num:
                entry['error'] = "Duplicate of entry on line %u" % line_num
                continue
            else:
                duplicate_catcher[ duplicate_catcher_key ] = reader.line_num
            
            # remove the above values from row
            for key in ['date','place_slug','category_slug']:
                del( row[key] )

            get_create_args = dict(
                place    = place,
                category = category,
                date     = date,
            )

            try:
                obj = cls.objects.get( **get_create_args )
            except cls.DoesNotExist:
                obj = cls( **get_create_args )
                
            # set the remaining attributes
            for key in row.keys():
                setattr( obj, key, row[key] )

            # check that the object is good
            try:
                obj.full_clean()
            except ValidationError as err:
                # this is hairy, but I can't seem to find better accessors to get at the messages.
                entry['error'] = ', '.join(["%s: %s" % (k,v[0]) for k,v in err.__dict__['message_dict'].items() ])
                continue

            entry['action'] = 'update' if obj.id else 'create'

            if save:
                obj.save()
                entry['action'] = 'saved'
                
            entry['obj'] = obj
        
        error_count = sum( [ 1 if i['error'] else 0 for i in entries ] )

        return {
            'error_count': error_count,
            'entries':     entries,
            'file_error':  None,
        }

    class Meta():
        ordering = ( '-date', 'category', 'place' )
        unique_together = ( 'place', 'category', 'date' )
        verbose_name_plural = 'data'
