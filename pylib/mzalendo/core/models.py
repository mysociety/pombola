import datetime
import re
from warnings import warn

from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django_date_extensions.fields import ApproximateDateField, ApproximateDate
from django.contrib.comments.moderation import CommentModerator, moderator
from django.db.models import Q

from tasks.models import Task
from images.models import HasImageMixin, Image

# tell South how to handle the custom fields 
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^django_date_extensions\.fields\.ApproximateDateField"])
add_introspection_rules([], ["^django.contrib\.gis\.db\.models\.fields\.PointField"])

date_help_text = "Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'"

class ModelBase(models.Model):
    
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now(), )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now(), )    

    def css_class(self):
        return self._meta.module_name

    class Meta:
       abstract = True      


class ContactKind(ModelBase):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]      


class Contact(ModelBase):

    kind    = models.ForeignKey('ContactKind')
    value   = models.TextField()
    note    = models.TextField(blank=True, help_text="publicly visible, use to clarify contact detail")
    source  = models.CharField(max_length=500, blank=True, default='', help_text="where did this contact detail come from")

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    def __unicode__(self):
        return "%s (%s for %s)" % ( self.value, self.kind, self.content_object )

    def generate_tasks(self):
        """generate tasks for ourselves, and for the foreign object"""
        Task.call_generate_tasks_on_if_possible( self.content_object )
        return []

    class Meta:
       ordering = ["content_type", "object_id", "kind", ]      


class InformationSource(ModelBase):
    source  = models.CharField(max_length=500)
    note    = models.TextField(blank=True)
    entered = models.BooleanField(default=False, help_text="has the information in this source been entered into this system?")

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    def __unicode__(self):
        return "%s: %s" % ( self.source, self.content_object )

    class Meta:
       ordering = ["content_type", "object_id", "source", ]      


class PersonQuerySet(models.query.GeoQuerySet):
    def is_mp(self):
        mp_title = PositionTitle.objects.get(slug='mp')
        return self.filter( position__title=mp_title )


class PersonManager(models.GeoManager):
    def get_query_set(self):
        return PersonQuerySet(self.model)


class Person(ModelBase, HasImageMixin):
    title           = models.CharField(max_length=100, blank=True)
    legal_name      = models.CharField(max_length=300)
    other_names     = models.TextField(blank=True, default='', help_text="other names the person might be known by - one per line")
    slug            = models.SlugField(max_length=200, unique=True, help_text="auto-created from first name and last name")
    gender          = models.CharField(max_length=1, choices=(('m','Male'),('f','Female')) )
    date_of_birth   = ApproximateDateField(blank=True, help_text=date_help_text)
    date_of_death   = ApproximateDateField(blank=True, help_text=date_help_text)
    original_id     = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to members in original mzalendo.com db')
    # religion
    # tribe

    contacts = generic.GenericRelation(Contact)
    images   = generic.GenericRelation(Image)
    objects  = PersonManager()
    
    def name(self):
        if self.other_names:
            return self.other_names.split("\n")[0]
        else:
            return self.legal_name
    
    def additional_names(self):
        if self.other_names:
            return self.other_names.split("\n")[1:]
        else:
            return []
    
    def is_mp(self):
        """Return true if this person is an MP"""
        return 'mp' in [ p.title.slug for p in self.position_set.all().currently_active() ]
        
    
    def __unicode__(self):
        return self.legal_name

    @models.permalink
    def get_absolute_url(self):
        return ( 'person', [ self.slug ] )
    
    def generate_tasks(self):
        """Generate tasks for missing contact details etc"""
        task_slugs = []
        
        wanted_contact_slugs = ['phone','email','address']
        have_contact_slugs = [ c.kind.slug for c in self.contacts.all() ]
        for wanted in wanted_contact_slugs:
            if wanted not in have_contact_slugs:
                task_slugs.append( "find-missing-" + wanted )
        
        return task_slugs
        
    class Meta:
       ordering = ["slug"]      


class OrganisationKind(ModelBase):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]      


class OrganisationQuerySet(models.query.GeoQuerySet):
    def parties(self):
        return self.filter(kind__slug='party')

    def active_parties(self):

        active_mp_positions     = Position.objects.all().filter(title__slug='mp'    ).currently_active()
        active_member_positions = Position.objects.all().filter(title__slug='member').currently_active()

        current_mps     = Person.objects.all().filter(position__in=active_mp_positions    ).distinct()
        current_members = Person.objects.all().filter(position__in=active_member_positions).distinct()

        return (
            self
                .parties()
                .filter( position__person__in=current_mps     )
                .filter( position__person__in=current_members )
                .distinct()                
        )


class OrganisationManager(models.GeoManager):
    def get_query_set(self):
        return OrganisationQuerySet(self.model)


class Organisation(ModelBase):
    name    = models.CharField(max_length=200)
    slug    = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary = models.TextField(blank=True, default='')
    kind    = models.ForeignKey('OrganisationKind')
    started = ApproximateDateField(blank=True, help_text=date_help_text)
    ended   = ApproximateDateField(blank=True, help_text=date_help_text)
    original_id = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to parties in original mzalendo.com db')

    objects  = OrganisationManager()
    contacts = generic.GenericRelation(Contact)

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.kind )

    @models.permalink
    def get_absolute_url(self):
        return ( 'organisation', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class PlaceKind(ModelBase):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]      


class Place(ModelBase):
    name         = models.CharField(max_length=200)
    slug         = models.SlugField(max_length=100, unique=True, help_text="created from name")
    kind         = models.ForeignKey('PlaceKind')
    shape_url    = models.URLField(verify_exists=True, blank=True )
    location     = models.PointField(null=True, blank=True)
    organisation = models.ForeignKey('Organisation', null=True, blank=True, help_text="use if the place uniquely belongs to an organisation - eg a field office" )
    original_id  = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to constituencies in original mzalendo.com db')

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.kind )

    @models.permalink
    def get_absolute_url(self):
        return ( 'place', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class PositionTitle(ModelBase):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = models.TextField(blank=True)
    original_id     = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to data in original mzalendo.com db')

    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ( 'position', [ self.slug ] )
    
    def organisations(self):
        """
        Return a qs of organisations, with the most frequently related first.

        Each organisation is also annotated with 'position_count' which might be
        useful.

        This is intended as an alternative to assigning a org to each
        position_title. Instead we can deduce it from the postions.
        """

        orgs = (
            Organisation
                .objects
                .filter(position__title=self)
                .annotate( position_count=models.Count('position') )
                .order_by( '-position_count' )
        )

        return orgs


    class Meta:
       ordering = ["slug"]      


class PositionQuerySet(models.query.GeoQuerySet):
    def currently_active(self):
        """Filter on start and end dates to limit to currently active postitions"""
        now = datetime.date.today()
        now_approx = ApproximateDate(year=now.year, month=now.month, day=now.day )

        return (
            self
              .filter( Q(start_date__lte=now_approx) )
              .filter( Q(  end_date__gte=now_approx) )
        )

    def currently_inactive(self):
        """Filter on start and end dates to limit to currently inactive postitions"""
        now = datetime.date.today()
        now_approx = ApproximateDate(year=now.year, month=now.month, day=now.day )
    
        return (
            self
              .filter( Q(  end_date__lte=now_approx) )
        )
    
    def political(self):
        """Filter down to only the political category"""
        return self.filter(category='political')

    def education(self):
        """Filter down to only the education category"""
        return self.filter(category='education')

    def other(self):
        """Filter down to only the other category"""
        return self.filter(category='other')

class PositionManager(models.GeoManager):
    def get_query_set(self):
        return PositionQuerySet(self.model)


class Position(ModelBase):
    category_choices = (
        ('political', 'Political'),
        ('education', 'Education (as a learner)'),
        ('other',     'Anything else'),
    )

    person          = models.ForeignKey('Person')
    organisation    = models.ForeignKey('Organisation', null=True, blank=True, )
    place           = models.ForeignKey('Place', null=True, blank=True, help_text="use if needed to identify the position - eg add constituency for an 'MP'" )
    title           = models.ForeignKey('PositionTitle', null=True, blank=True, )
    subtitle        = models.CharField(max_length=200, blank=True, default='')
    category        = models.CharField(max_length=20, choices=category_choices, default='other', help_text="What sort of position was this?")
    note            = models.CharField(max_length=300, blank=True, default='', )
    start_date      = ApproximateDateField(blank=True, help_text=date_help_text)
    end_date        = ApproximateDateField(blank=True, help_text=date_help_text, default="future")
    
    objects = PositionManager()


    def display_dates(self):
        """Nice HTML for the display of dates"""

        # no dates
        if not (self.start_date or self.end_date):
            return ''

        # start but no end
        if self.start_date and not self.end_date:
            return "Started %s" % self.start_date

        # both dates
        if self.start_date and self.end_date:
            if self.end_date.future:
                return "Started %s" % ( self.start_date )
            else:
                return "%s &rarr; %s" % ( self.start_date, self.end_date )
        
        # end but no start
        if not self.start_date and self.end_date:
            return 'ongoing'

    def display_start_date(self):
        """Return text that represents the start date"""
        if self.start_date:
            return str(self.start_date)
        return '?'
    
    def display_end_date(self):
        """Return text that represents the end date"""
        if self.end_date:
            return str(self.end_date)
        return '?'

    def is_ongoing(self):
        """Return True or False for whether the position is currently ongoing"""
        if not self.end_date:
            return False
        elif self.end_date.future:
            return True
        else:
            # turn today's date into an ApproximateDate object and cmp to that
            now = datetime.date.today()
            now_approx = ApproximateDate(year=now.year, month=now.month, day=now.day )
            return now_approx <= self.end_date

    def has_known_dates(self):
        """Is there at least one known (not future) date?"""
        return (self.start_date and not self.start_date.future) or (self.end_date and not self.end_date.future)
    
    def __unicode__(self):

        title = self.title or '???'

        if self.organisation:
            organisation = self.organisation.name
        else:
            organisation = '???'

        return "%s (%s at %s)" % ( self.person.name(), title, organisation)

    class Meta:
        ordering = ['-end_date', '-start_date']  

class GenericModerator(CommentModerator):
    email_notification = False

    def moderate(self, comment, content_object, request):
        """Require moderation unless user is in Trusted group"""
        user = request.user

        try:
            user.groups.get(name='Trusted')
            return False
        except:
            return True

# this models.py might be getting loaded several times
# http://stackoverflow.com/questions/3277474//3343654#3343654
if Person not in moderator._registry:
    moderator.register(Person, GenericModerator)

