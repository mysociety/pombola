import re

from django.db import models

from core.models import Person
from hansard.models import Sitting

class Entry(models.Model):
    """Model for representing an entry in Hansard - speeches, headings etc"""

    type_choices = (
        ('heading', 'Heading'),
        ('scene',   'Description of event'),
        ('speech',  'Speech'),
        ('other',   'Other'),
    )

    type          = models.CharField( max_length=20, choices=type_choices )
    sitting       = models.ForeignKey( Sitting )

    # page_number is the page that this appeared on in the source.
    page_number   = models.IntegerField( blank=True )
    
    # Doesn't really mean anything - just a counter so that for each sitting we
    # can display the entries in the correct order. 
    text_counter  = models.IntegerField()

    # Speakers only apply to the 'speech' type. For those we should always have
    # a name and possibly a title. Other code may then take those and try to
    # link the speech up to a person.
    speaker_name  = models.CharField( max_length=200, blank=True )
    speaker_title = models.CharField( max_length=200, blank=True )
    speaker       = models.ForeignKey( Person, blank=True, null=True )

    # What was actually said
    content       = models.TextField()

    def __unicode__(self):
        return "%s: %s" % (self.type, self.content[:100])
    
    class Meta:
        ordering = ['sitting', 'text_counter']
        app_label = 'hansard'
        verbose_name_plural = 'entries'
        
    @classmethod
    def assign_speakers(cls):
        """Go through all entries and assign speakers"""
        
        entries = cls.objects.filter(
            speaker__isnull= True,
            type           = 'speech',
        ).exclude(
            speaker_name   = '',
        )

        for entry in entries:
            print '----------------'

            name = entry.speaker_name
            print name
            
            # drop the prefix
            name = re.sub( r'^\w+\.\s', '', name )
            print name
            
            
            person_search = Person.objects.filter(legal_name__icontains=name)

            if person_search.count() == 1:
                print "Found match: " + person_search[0].name()
                entry.speaker = person_search[0]
                entry.save()
            elif person_search.count() > 1:
                print "Found more than one match:"
                for p in person_search:
                    print "\t" + p.name()
            else:
                print "Found no matches"


