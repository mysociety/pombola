import re

from django.db import models
from django.core.urlresolvers import reverse

from pombola.core.models import Person
from pombola.hansard.models import Sitting, Alias
from pombola.hansard.models.base import HansardModelBase


class EntryQuerySet(models.query.QuerySet):
    def monthly_appearance_counts(self):
        """Return an list of dictionaries for dates and counts for each month"""

        # would prefer to do this as a single query but I can't seem to make the ORM do that.

        dates = self.dates('sitting__start_date','month', 'DESC')
        counts = []
        
        for d in dates:
            qs = self.filter(sitting__start_date__month=d.month, sitting__start_date__year=d.year)
            counts.append(dict(date=d, count=qs.count()))

        return counts
        
    def unassigned_speeches(self):
        """All speeches that do not have a speaker assigned"""
        return self.filter(
            speaker__isnull = True,
            type            = 'speech',
        ).exclude(
            speaker_name = '',
        )

class EntryManager(models.Manager):
    def get_query_set(self):
        return EntryQuerySet(self.model)
    

class Entry(HansardModelBase):
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
        sitting_url = self.sitting.get_absolute_url()
        return "%s#entry-%u" % (sitting_url, self.id)

    def css_class(self):
        return 'hansard_entry'

    class Meta:
        ordering = ['sitting', 'text_counter']
        app_label = 'hansard'
        verbose_name_plural = 'entries'
        
    @classmethod
    def assign_speakers(cls):
        """Go through all entries and assign speakers"""
        
        entries = cls.objects.all().unassigned_speeches()
        # entries = entries.filter(speaker_name__icontains='Speaker')
        # create an in memory cache of speaker names and the sitting dates, to
        # avoid hitting the db as badly with all the repeated requests
        cache = {}

        for entry in entries:
            cache_key = "%s-%s" % (entry.sitting.start_date, entry.speaker_name)

            if cache_key in cache:
                speakers = cache[cache_key]
            else:
                speakers = entry.possible_matching_speakers(update_aliases=True)
                if not speakers:
                    speakers = entry.possible_matching_speakers2() 

            if speakers and len(speakers) == 1:
                speaker = speakers[0]
                entry.speaker = speaker
                entry.save()                
                    
    def possible_matching_speakers2(self):
        alias = Alias.objects.filter(alias=self.speaker_name)
        if len(alias):
            alias = alias[0]

            person = alias.person
            if person:
                speakers = Person.objects.filter(id=person.id)
                cache[cache_key] = speakers
                return speakers
        return None

    def possible_matching_speakers(self, update_aliases=False):
        """
        Return array of person objects that might be the speaker.

        If 'update_aliases' is True (False by default) and the name cannot be
        ignored then an entry will be made in the alias table that so that the
        alias is inspected by an admin.
        """

        name = self.speaker_name
        name = Alias.clean_up_name( name )
        
        # First check for a matching alias that is not ignored
        try:
            alias = Alias.objects.get( alias=name )
            
            if alias.ignored:
                # if the alias is ignored we should not match anything
                return []
            elif alias.person:
                return [ alias.person ]
            elif alias.is_unassigned:
                # Pretend that this alias does not exist so that it is checked
                # in case new people have been added to the database since the
                # last run.
                pass
            else:
                return []

        except Alias.DoesNotExist:
            alias = None
        
        # drop the prefix
        stripped_name = re.sub( r'^\w+\.\s', '', name )
        
        person_search = (
            Person
            .objects
            .all()
            .is_politician( when=self.sitting.start_date )
            .filter(legal_name__icontains=stripped_name)
            .distinct()
        )
        
        results = person_search.all()[0:]
        
        found_one_result = len(results) == 1

        # If there is a single matching speaker and an unassigned alias delete it
        if found_one_result and alias and alias.is_unassigned:
            alias.delete()
            
        # create an entry in the aliases table if one is needed
        if not alias and update_aliases and not found_one_result and not Alias.can_ignore_name(name):
            Alias.objects.create(
                alias   = name,
                ignored = False,
                person  = None,
            )
        
        return results


