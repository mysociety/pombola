import datetime
import re
from warnings import warn

from django.core import exceptions
from django.core.urlresolvers import reverse

from django.db.models import Q

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models

from haystack.query import SearchQuerySet

from markitup.fields import MarkupField

from django_date_extensions.fields import ApproximateDateField, ApproximateDate
from tasks.models import Task
from images.models import HasImageMixin, Image
from comments2.models import Comment

from scorecards.models import ScorecardMixin

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


    def get_admin_url(self):
        url = reverse(
            'admin:%s_%s_change' % ( self._meta.app_label, self._meta.module_name),
            args=[self.id]
        )
        return url
    

    class Meta:
       abstract = True      


class ManagerBase(models.GeoManager):
    def update_or_create(self, filter_attrs, attrs):
        """Given unique look-up attributes, and extra data attributes, either
        updates the entry referred to if it exists, or creates it if it doesn't.
        
        Returns the object updated or created, having saved the changes.
        """
        try:
            obj = self.get(**filter_attrs)
            changed = False
            for k, v in attrs.items():
                if obj.__dict__[k] != v:
                    changed = True
                    obj.__dict__[k] = v
            if changed:
                obj.save()
        except exceptions.ObjectDoesNotExist:
            attrs.update(filter_attrs)
            obj = self.create(**attrs)
            obj.save()
        
        return obj

    



class ContactKind(ModelBase):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")

    objects = ManagerBase()

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
    
    objects = ManagerBase()

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
    
    objects = ManagerBase()

    def __unicode__(self):
        return "%s: %s" % ( self.source, self.content_object )

    class Meta:
       ordering = ["content_type", "object_id", "source", ]      


class PersonQuerySet(models.query.GeoQuerySet):
    def is_mp(self, when=None):
        
        mp_qs = Position.objects.filter( title__slug='mp' ).currently_active( when )

        qs = self.filter( position__in = mp_qs )
        return qs


class PersonManager(ManagerBase):
    def get_query_set(self):
        return PersonQuerySet(self.model)
    
    def loose_match_name(self, name):
        """Search for a loose match on a name. May not be too reliable"""

        # Try matching all the bits
        results = SearchQuerySet().filter_and( content=name ).models( self.model )

        # if that fails try matching all the bits in any order
        if not len( results ):
            results = SearchQuerySet().models(Person)
            for bit in re.split(r'\s+', name):
                results = results.filter_and( content=bit )

        # If we have exactly one result return that
        if len( results ) == 1:
            return results[0].object
        else:
            return None
        

class Person(ModelBase, HasImageMixin, ScorecardMixin ):
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
    summary         = MarkupField(blank=True, default='')

    contacts = generic.GenericRelation(Contact)
    images   = generic.GenericRelation(Image)
    objects  = PersonManager()

    comments = generic.GenericRelation(Comment)
    
    def clean(self):
        # strip other_names and flatten multiple newlines
        self.other_names = re.sub(r"\n+", "\n", self.other_names ).strip()
        
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
    
            
    def mp_positions(self):
        return self.position_set.all().currently_active().filter(title__slug='mp')
            

    def is_mp(self):
        """Return the mp position if this person is an MP, else None"""
        try:
            return self.mp_positions()[0]
        except IndexError:
            return None


    def parties(self):
        """Return list of parties that this person is currently a member of"""
        party_memberships = self.position_set.all().currently_active().filter(title__slug='member').filter(organisation__kind__slug='party')
        parties = [ x.organisation for x in party_memberships ]
        return parties
    

    def constituencies(self):
        """Return list of constituencies that this person is currently an MP for"""
        constituencies = [ x.place for x in self.mp_positions() if x.place ]
        return constituencies

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
    summary         = MarkupField(blank=True, default='')

    objects = ManagerBase()

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


class OrganisationManager(ManagerBase):
    def get_query_set(self):
        return OrganisationQuerySet(self.model)


class Organisation(ModelBase):
    name    = models.CharField(max_length=200)
    slug    = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
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
    summary         = MarkupField(blank=True, default='')

    objects = ManagerBase()

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
    mapit_id     = models.PositiveIntegerField(blank=True, null=True)
    parent_place = models.ForeignKey('self', blank=True, null=True, related_name='child_places')

    objects = ManagerBase()

    def parent_places(self):
        """Return a list of parents, with top parent first."""
        if not self.parent_place:
            return []
        parents = self.parent_place.parent_places()
        parents.append( self.parent_place )
        return parents

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.kind )
    
    def current_mp_position(self):
        """Return the current MP position, or None"""
        qs = self.position_set.filter(title__slug='mp').currently_active()
        try:
            return qs[0]
        except IndexError:
            return None

    @models.permalink
    def get_absolute_url(self):
        return ( 'place', [ self.slug ] )

    class Meta:
       ordering = ["slug"]      


class PositionTitle(ModelBase):
    name            = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary         = MarkupField(blank=True, default='')
    original_id     = models.PositiveIntegerField(blank=True, null=True, help_text='temporary - used to link to data in original mzalendo.com db')
    requires_place  = models.BooleanField(default=False, help_text="Does this job title require a place to complete the position?")

    objects = ManagerBase()

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
    def currently_active( self, when=None ):
        """Filter on start and end dates to limit to currently active postitions"""

        if when == None: when = datetime.date.today()
        now_approx = ApproximateDate( year=when.year, month=when.month, day=when.day )

        qs = (
            self
                .filter( start_date__lte = now_approx )
                .filter( Q( end_date__gte = now_approx ) | Q( end_date = '' ) )
        )

        return qs


    def currently_inactive( self, when=None ):
        """Filter on start and end dates to limit to currently inactive postitions"""
    
        if when == None: when = datetime.date.today()
        now_approx = ApproximateDate( year=when.year, month=when.month, day=when.day )
    
        start_criteria = Q( start_date__gt = now_approx )
        end_criteria   = Q( end_date__lt   = now_approx ) & ~Q(end_date = '')
        
        qs = self.filter( start_criteria | end_criteria )

        return qs
    

    def political(self):
        """Filter down to only the political category"""
        return self.filter(category='political')

    def education(self):
        """Filter down to only the education category"""
        return self.filter(category='education')

    def other(self):
        """Filter down to only the other category"""
        return self.filter(category='other')

class PositionManager(ManagerBase):
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

    # Two hidden fields that are only used to do sorting. Filled in by code.
    sorting_start_date      = models.CharField(editable=True, default='', max_length=10)
    sorting_end_date        = models.CharField(editable=True, default='', max_length=10)
    
    objects = PositionManager()

    def clean(self):
        if not (self.organisation or self.title or self.place):
            raise exceptions.ValidationError('Must have at least one of organisation, title or place.')

        if self.title and self.title.requires_place and not self.place:
            raise exceptions.ValidationError( "The job title '%s' requires a place to be set" % self.title.name )
            

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
    

    def _set_sorting_dates(self):
        """Set the sorting dates from the actual dates (does not call save())"""
        # value can be yyyy-mm-dd, future or None
        start = repr( self.start_date ) if self.start_date else ''
        end   = repr( self.end_date   ) if self.end_date   else ''
        
        # set the value or default to something sane
        sorting_start_date =        start or '0000-00-00'
        sorting_end_date   = end or start or '0000-00-00'
        
        # To make the sorting consistent special case some parts
        if not end and start == 'future':
            sorting_start_date = 'a-future' # come after 'future'
        
        self.sorting_start_date = sorting_start_date
        self.sorting_end_date   = sorting_end_date
        
        return True

    def save(self, *args, **kwargs):
        self._set_sorting_dates()
        super(Position, self).save(*args, **kwargs)

    def __unicode__(self):

        title = self.title or '???'

        if self.organisation:
            organisation = self.organisation.name
        else:
            organisation = '???'

        return "%s (%s at %s)" % ( self.person.name(), title, organisation)

    class Meta:
        ordering = ['-sorting_end_date', '-sorting_start_date']  
