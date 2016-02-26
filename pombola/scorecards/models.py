import datetime
import dateutil.parser
import csv

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from markitup.fields import MarkupField


class Category(models.Model):
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now, )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now, )

    name        = models.CharField( max_length=200, unique=True )
    slug        = models.SlugField( unique=True )
    synopsis    = models.CharField( max_length=200 )
    description = MarkupField()
    
    def __unicode__(self):
        return self.name
    
    class Meta():
        ordering = ( 'name', )
        verbose_name_plural = 'categories'


class Entry(models.Model):
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now, )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now, )

    category = models.ForeignKey(Category)

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Used to select the most recent data of this category. Require a full data
    # for simplicity.
    date = models.DateField()

    # Used to manually stop a scorecard being shown. If disabled is true then there
    # the scorecard will not count towards the totals. If there is a comment a
    # placeholder will be shown with the comment text, if comment is blank (the
    # default) then nothing will be shown.    
    disabled         = models.BooleanField(default=False)
    disabled_comment = models.CharField(
        max_length = 300,
        blank      = True,
        default    = '',
        help_text  = "A comment to explain why the scorecard is disabled - eg 'No data is available'",
    )

    # place, category, date are unique so can be used to update/overwrite
    # information when doing a CSV upload - see unique_together in Meta below.

    remark = models.CharField(
        max_length=150,
    )

    extended_remark = MarkupField(
        max_length = 1000,
        blank = True,
        help_text = "Extra details about the entry, not shown in summary view.",
    )

    score = models.IntegerField(
        choices = (
            ( +1, 'Good (+1)'   ),
            (  0, 'Neutral (0)' ),
            ( -1, 'Bad (-1)'    ),
        ),
    )

    equivalent_remark = MarkupField(
        max_length = 400,
        blank = True,
        help_text = 'Please **bold** the relevant part - eg "Enough money is going missing to pay for **123 teachers**"',
    )  
    
    # Every data point can have an external source. 
    source_url = models.URLField(blank=True)  
    source_name = models.CharField(max_length=200, blank=True)

    class Meta():
        ordering = ('-date', 'category')
        unique_together = ('content_type', 'object_id', 'category', 'date')
        verbose_name_plural = 'entries'
    

    def __unicode__(self):
        return '%s for %s (%s)' % (self.category, self.content_object, self.date)

    def score_as_word(self):
        return self.score_to_word(self.score)

    # it's useful if the template can detect if there are additional details that might need to be displayed
    def has_details(self):
        return (self.equivalent_remark or self.extended_remark or self.source_url )
        
    @classmethod
    def score_to_word(cls, score):
        if   score >=  0.5: return 'good'
        elif score <= -0.5: return 'bad'
        else:               return 'average'  # TODO - should be neutral (change once design work is done)

    @classmethod
    def process_csv(cls, csv_file, save=False):
        """
        Take a CSV file and process the entries. Returns a results hash with
        errors and data objects. If 'save' is True the database is updated.
        """
        reader = csv.DictReader(csv_file)
    
        entries = []
        duplicate_catcher = {} # key is category_id-place_id-date, val is line number
    
        # check that the headers are what we expect
    
        expected_headers = set([
                'category_slug', 'date', 'score',
                'remark', 'extended_remark', 'equivalent_remark',
                'source_url', 'source_name',
                ])
        actual_headers = set(reader.fieldnames)

        errors = {}
        if not expected_headers.issubset(actual_headers):
            # try to produce a friendly error
            missing = expected_headers - actual_headers
            if missing:
                file_error = 'Missing expected header(s): %s' % ', '.join(missing)
            errors["file_error"] = file_error

        # if 'place_slug' in actual_headers:
        #     pass
        # # Other types of object which things could link to can be added in elifs here.
        # else:
        #     errors["file_error"] = "Expecting a place_slug. Supply a place_slug column, or get a different type added."
            
        # if errors:
        #     return errors

        for row in reader:
            entry = dict(
                line_number=reader.line_num,
                error=None,
                action=None,
            )
            entries.append(entry)
    
            # Extract the values that need to be inflated
            if 'place_slug' in actual_headers:
                # Not really a nice place for an import, but avoids a loop.
                from pombola.core.models import Place
                
                try:
                    content_object = Place.objects.get(slug=row['place_slug'])
                except Place.DoesNotExist:
                    entry['error'] = "place slug not found"
                    continue

            try:
                category = Category.objects.get(slug=row['category_slug'])
            except Category.DoesNotExist:
                entry['error'] = "category slug not found"
                continue
                
            try:
                # FIXME - use fuzzy.
                date = dateutil.parser.parse(row['date']).date()
            except ValueError:
                entry['error'] = "date: Not a valid yyyy/mm/dd date: '%s'" % row['date']
                continue
    
            # check that we've not seen this entry before in this file
            duplicate_catcher_key = '-'.join([ str(content_object.id), str(category.id), str(date) ])
            line_num = duplicate_catcher.get(duplicate_catcher_key)
            if line_num:
                entry['error'] = "Duplicate of entry on line %u" % line_num
                continue
            else:
                duplicate_catcher[duplicate_catcher_key] = reader.line_num
            
            # remove the above values from row
            for key in ['date','place_slug','category_slug']:
                del(row[key])

            get_create_args = {
                "content_type": ContentType.objects.get_for_model(content_object),
                "object_id": content_object.id,
                "category": category,
                "date": date,
            }
    
            try:
                obj = cls.objects.get(**get_create_args)
            except cls.DoesNotExist:
                obj = cls(**get_create_args)

            # set the remaining attributes
            for key in row.keys():
                setattr(obj, key, row[key])
    
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


class ScorecardMixin(models.Model):
    """Mixin to add scorecard related methods to models"""

    # TODO - we should limit the scorecards to the newest in each category

    scorecard_entries = GenericRelation(Entry)

    # Show an overall score for this Item.
    # Set this to false in anything for which you only want the individual
    # scores and no average.
    is_overall_scorecard_score_applicable = True

    @property
    def show_overall_score(self):
        """Should we show an overall score? Yes if applicable and there are active scorecards"""
        return self.is_overall_scorecard_score_applicable and self.active_scorecards().exists()
        
    def active_scorecards(self):
        return self.scorecard_entries.filter(disabled=False)

    def visible_scorecards(self):
        """All scorecards, except disabled ones with no comment"""
        return self.scorecard_entries.exclude(disabled=True, disabled_comment='')

    def scorecard_overall(self):
        return self.active_scorecards().aggregate(models.Avg('score'))['score__avg']

    def scorecard_overall_as_word(self):
        return Entry.score_to_word(self.scorecard_overall())
        
    def has_scorecards(self):
        return self.visible_scorecards().exists()

    def scorecards(self):
        return self.visible_scorecards()
    
    class Meta:
       abstract = True



# This is code to paste into the shell to create entries for all the
# constiteuncies that do not have NTA data.

# import datetime
# from pombola.core.models import Place
# from pombola.scorecards.models import Category, Entry
# 
# nta_cat = Category.objects.get(slug='cdf-performance')
# 
# for cons in Place.objects.all().constituencies():
# 
#     if Entry.objects.filter(place=cons, category=nta_cat).exists():
#         print 'skipping ' + cons.name
#     else:
#         print 'adding disabled entry for ' + cons.name        
#         Entry(
#             content_object=cons,
#             category=nta_cat,
#             date = datetime.date.today(),
#             disabled=True,
#             disabled_comment = "The NTA have not audited CDF spending in %s for a year when the current MP was in office." % cons.name,
#             remark = 'dummy text',
#             score = 0,
#         ).save()

