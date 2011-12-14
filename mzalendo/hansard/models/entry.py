import re

from django.db import models

from core.models import Person
from hansard.models import Sitting, Alias

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
            speaker__isnull = True,
            type            = 'speech',
        ).exclude(
            speaker_name = '',
        )
        
        # create an in memory cache of speaker names and the sitting dates, to
        # avoid hitting the db as badly with all the repeated requests
        cache = {}

        for entry in entries:
            # print '--------- ' + entry.speaker_name + ' ---------'

            cache_key = "%s-%s" % (entry.sitting.start_date, entry.speaker_name)

            if cache_key in cache:
                speakers = cache[cache_key]
            else:
                speakers = entry.possible_matching_speakers()
                cache[cache_key] = speakers

            if len(speakers) == 1:
                speaker = speakers[0]
                entry.speaker = speaker
                entry.save()


    def possible_matching_speakers(self):
        """Return array of person objects that might be the speaker"""

        name = self.speaker_name
        
        # First check for a matching alias
        # try:
        try:
            alias = Alias.objects.get( alias=name )
            return [ alias.person ]
        except Alias.DoesNotExist:
            pass

        # drop the prefix
        name = re.sub( r'^\w+\.\s', '', name )
        
        person_search = (
            Person
            .objects
            .all()
            .is_mp( when=self.sitting.start_date )
            .filter(legal_name__icontains=name)
        )

        return person_search.all()[0:]

