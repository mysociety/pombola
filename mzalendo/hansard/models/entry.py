import re

from django.db import models
from django.core.urlresolvers import reverse

from core.models import Person
from hansard.models import Sitting, Alias


class EntryQuerySet(models.query.QuerySet):
    def monthly_appearance_counts(self):
        """return an array of hasher for date ad counts for each month"""

        # would prefer to do this as a single query but I can't seem to make the ORM do that.

        dates = self.dates('sitting__start_date','month', 'DESC' )
        counts = []
        
        for d in dates:
            qs = self.filter(sitting__start_date__month=d.month, sitting__start_date__year=d.year )
            counts.append(
                dict( date=d, count=qs.count() )
            )

        return counts
        
    def unassigned_speeches(self):
        """All speeches that do not have a speaker assigned"""
        return self.filter(
            speaker__isnull = True,
            type            = 'speech',
        ).exclude(
            speaker_name = '',
        )
    
    def unassigned_speaker_names(self):
        unassigned_names = (
            Entry.objects
                .all()
                .unassigned_speeches()
                .values('speaker_name')
                .order_by('speaker_name')
                .exclude( speaker_name__in=Alias.objects.values('alias') )
                .distinct()
        )

        names = [
            x['speaker_name']
            for x
            in unassigned_names
            if not Entry.can_ignore_name(x['speaker_name'])
        ]

        return names


class EntryManager(models.Manager):
    def get_query_set(self):
        return EntryQuerySet(self.model)
    

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
    speaker       = models.ForeignKey( Person, blank=True, null=True, related_name='hansard_entries' )

    # What was actually said
    content       = models.TextField()

    objects = EntryManager()

    def __unicode__(self):
        return "%s: %s" % (self.type, self.content[:100])
    
    def get_absolute_url(self):
        url = reverse(
            'hansard:sitting_view',
            kwargs={ 'pk': self.sitting.id },
        )
        return "%s#entry-%u" % (url, self.id)


    class Meta:
        ordering = ['sitting', 'text_counter']
        app_label = 'hansard'
        verbose_name_plural = 'entries'
        
    @classmethod
    def assign_speakers(cls):
        """Go through all entries and assign speakers"""
        
        entries = cls.objects.all().unassigned_speeches()
        
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
        
        # First check for a matching alias that is not ignored
        try:
            alias = Alias.objects.get( alias=name )
            
            if alias.ignored:
                return []
            else:
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
        if re.match(r'\(.\)', name):
            return True

        # Ignore anything that looks like an parliamentary support role
        if re.search( r'\bTellers\b', name):
            return True

        return False
