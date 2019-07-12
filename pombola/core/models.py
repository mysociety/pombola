from __future__ import division

import calendar
import datetime
from functools import partial
import re
import itertools
import random
from collections import defaultdict

from django.core import exceptions
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator

from django.db.models import Q
from django.db import transaction
from django.db.models.signals import post_init

from django.utils.dateformat import DateFormat

from django.contrib.contenttypes.fields import (
    GenericRelation, GenericForeignKey
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models

from django.db.models.fields import DateField

from markitup.fields import MarkupField

from django_date_extensions.fields import ApproximateDateField, ApproximateDate

from slug_helpers.models import validate_slug_not_redirecting
from images.models import HasImageMixin, Image

from pombola.tasks.models import Task

from pombola.scorecards.models import ScorecardMixin
from pombola.budgets.models import BudgetsMixin

from mapit import models as mapit_models

from pombola.country import significant_positions_filter

date_help_text = "Format: '2011-12-31', '31 Jan 2011', 'Jan 2011' or '2011' or 'future'"

def validate_person_slug(slug):
    return validate_slug_not_redirecting('core', 'Person', slug)

def validate_organisation_slug(slug):
    return validate_slug_not_redirecting('core', 'Organisation', slug)

def validate_place_slug(slug):
    return validate_slug_not_redirecting('core', 'Place', slug)


# FIXME: Ideally this should be in django_date_extensions; we should
# make a pull request to include it.
def approximate_date_to_date(approx_date, assume):
    """Convert an approximate date to the earliest or latest date it could mean

    'assume' should be either 'earliest' or 'latest' to indicate
    whether this function should return the earliest or latest
    possible date that might be indicated by the approximate date.

    For example:

    >>> approximate_date_to_date(ApproximateDate(year=2003), assume='earliest')
    datetime.date(2003, 1, 1)
    >>> approximate_date_to_date(ApproximateDate(year=2003), assume='latest')
    datetime.date(2003, 12, 31)

    >>> approximate_date_to_date(ApproximateDate(year=2004, month=2), assume='earliest')
    datetime.date(2004, 2, 1)
    >>> approximate_date_to_date(ApproximateDate(year=2004, month=2), assume='latest')
    datetime.date(2004, 2, 29)

    >>> approximate_date_to_date(None, assume='earliest')
    datetime.date(1, 1, 1)
    >>> approximate_date_to_date(None, assume='latest')
    datetime.date(9999, 12, 31)

    >>> approximate_date_to_date(ApproximateDate(past=True), assume='earliest')
    datetime.date(1, 1, 1)
    >>> approximate_date_to_date(ApproximateDate(past=True), assume='latest')
    datetime.date(1, 1, 1)

    >>> approximate_date_to_date(ApproximateDate(future=True), assume='earliest')
    datetime.date(9999, 12, 31)
    >>> approximate_date_to_date(ApproximateDate(future=True), assume='latest')
    datetime.date(9999, 12, 31)

    """
    if assume not in ('earliest', 'latest'):
        raise ValueError("approx_end must be either 'earliest' or 'latest'")
    earliest = (assume == 'earliest')
    if (earliest and not approx_date) or (approx_date and approx_date.past):
        return datetime.date.min
    if (not earliest and not approx_date) or (approx_date and approx_date.future):
        return datetime.date.max
    year, month, day = approx_date.year, approx_date.month, approx_date.day
    # If we just have a year:
    if month == 0 and day == 0:
        if earliest:
            return datetime.date(year, 1, 1)
        else:
            return datetime.date(year, 12, 31)
    # If we just have a month and a year:
    if day == 0:
        if earliest:
            return datetime.date(year, month, 1)
        else:
            last_day = calendar.monthrange(year, month)[1]
            return datetime.date(year, month, last_day)
    # Otherwise we must have a complete date:
    return datetime.date(year, month, day)

def get_latest_day_of_year(year):
    """
    Return a date object for the last day of the year, or today if it's the current year.
    Will fail if a future year is passed.
    """
    year_end_date = datetime.date(year, 12, 31)
    today = datetime.date.today()
    if year > today.year:
        raise ValueError("year cannot be later than the current year.")
    return min(today, year_end_date)


class ModelBase(models.Model):
    created = models.DateTimeField( auto_now_add=True )
    updated = models.DateTimeField( auto_now=True )

    fields_to_whitespace_normalize = []

    def save(self, *args, **kwargs):
        self.normalize_whitespace()
        super(ModelBase, self).save(*args, **kwargs)

    def normalize_whitespace(self):
        for field in self.fields_to_whitespace_normalize:
            previous = getattr(self, field)
            normalized = re.sub(r'(?ms)\s+', ' ', previous).strip()
            setattr(self, field, normalized)

    def css_class(self):
        return self._meta.model_name

    def get_admin_url(self):
        url = reverse(
            'admin:%s_%s_change' % ( self._meta.app_label, self._meta.model_name),
            args=[self.id]
        )
        return url

    def get_disqus_thread_data(self, request):
        return {
            'disqus_canonical_url':
            request.build_absolute_uri(self.get_absolute_url()),
            'disqus_identifier':
            '{0}-{1}'.format(self.css_class(), self.id)
        }

    def get_popolo_id(self, id_scheme):
        table_name = self._meta.db_table
        return '{1}:{2}'.format(id_scheme, table_name, self.id)

    @property
    def show_active(self):
        """Used to indicate whether results in search should be greyed out"""
        return True

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


class Identifier(ModelBase):
    """This model represents alternative identifiers for objects"""

    scheme = models.CharField(max_length=200)
    identifier = models.CharField(max_length=500)

    content_type = models.ForeignKey(
        ContentType, related_name='pombola_identifier_set'
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = ManagerBase()

    def __unicode__(self):
        return '"%s%s"' % (self.scheme, self.identifier)

    class Meta:
        unique_together = ('scheme', 'identifier')


class IdentifierMixin(object):

    """Useful methods for objects that may be referred to by an Indentifier"""

    def get_identifier(self, scheme):
        """Returns the identifier in a particular scheme for this object

        If there is no identifier for this object in that scheme, then
        None is returned. If there is more than one identifier found,
        then an exception is thrown."""
        try:
            identifier = Identifier.objects.get(
                content_type = ContentType.objects.get_for_model(self),
                scheme=scheme,
                object_id=self.id)
            return identifier.identifier
        except exceptions.ObjectDoesNotExist:
            return None

    def get_identifiers(self, scheme):
        """Returns all identifiers in a particular scheme for this object"""

        return Identifier.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            scheme=scheme,
            object_id=self.id).values_list('identifier', flat=True)

    def get_all_identifiers(self):
        """Return all identifiers for this object in any scheme

        This returns a dict which maps a scheme to a set of
        identifiers."""
        # get_for_model caches results, so there should only be one
        # database hit per model
        results = defaultdict(set)
        for identifier in self.identifiers.all():
            results[identifier.scheme].add(identifier.identifier)
        return results


class ContactKind(ModelBase):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="created from name")

    fields_to_whitespace_normalize = ['name']

    objects = ManagerBase()

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]


class Contact(ModelBase):
    kind = models.ForeignKey('ContactKind')
    value = models.TextField()
    note = models.TextField(blank=True, help_text="publicly visible, use to clarify contact detail")
    source = models.CharField(max_length=500, blank=True, default='', help_text="where did this contact detail come from")

    preferred = models.BooleanField(help_text="Should this contact detail be listed before others of the same type?")

    # link to other objects using the ContentType system
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    fields_to_whitespace_normalize = ['value']

    objects = ManagerBase()

    def __unicode__(self):
        return "%s (%s for %s)" % (self.value, self.kind, self.content_object)

    def generate_tasks(self):
        """generate tasks for ourselves, and for the foreign object"""
        Task.call_generate_tasks_on_if_possible(self.content_object)
        return []

    class Meta:
       ordering = ["content_type", "-preferred", "object_id", "kind"]


class InformationSource(ModelBase):
    source = models.CharField(max_length=500)
    note = models.TextField(blank=True)
    entered = models.BooleanField(default=False, help_text="has the information in this source been entered into this system?")

    # link to other objects using the ContentType system
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    fields_to_whitespace_normalize = ['source']

    objects = ManagerBase()

    def __unicode__(self):
        return "%s: %s" % (self.source, self.content_object)

    class Meta:
       ordering = ["content_type", "object_id", "source"]


class PersonQuerySet(models.query.GeoQuerySet):
    def is_politician(self, when=None):
        # FIXME - Don't like the look of this, rather a big subquery.
        return self.filter(position__in=Position.objects.all().current_politician_positions(when))

class PersonManager(ManagerBase):
    def get_queryset(self):
        return PersonQuerySet(self.model)

    def loose_match_name(self, name):
        """Search for a loose match on a name. May not be too reliable"""

        # import here to avoid creating an import loop
        from haystack.query import SearchQuerySet

        # Try matching all the bits
        results = SearchQuerySet().filter_and(content=name).models(self.model)

        # if that fails try matching all the bits in any order
        if not len(results):
            results = SearchQuerySet().models(Person)
            for bit in re.split(r'\s+', name):
                results = results.filter_and(content=bit)

        # If we have exactly one result return that
        if len(results) == 1:
            return results[0].object
        else:
            return None

    def get_by_slug_or_id(self, identifier):
        try:
            return self.get(slug=identifier)
        except self.model.DoesNotExist:
            try:
                person_id = int(identifier)
            except ValueError:
                raise self.model.DoesNotExist, "Person matching query does not exist."
            return self.get(pk=person_id)

    def get_featured(self):
        # select all the presidential aspirants
        return self.filter(can_be_featured=True)

    def get_next_featured(self, current_slug, want_previous=False):
        """ Returns the next featured person, in slug order: using slug order because it's unique and easy to
            exclude the current person.

            If no slug is provided, returns a random person.
            If the slug is purely numeric (n), this consistently returns a person (actually the nth wrapping around
            where necessary): this allows js to generate random calls that can nonetheless be served from the cache.\
        """

        # original code that selects based on the can_be_featured flag
        # all_results = self.filter(can_be_featured=True)

        # select all the presidential aspirants
        all_results = self.get_featured()

        if not all_results.exists():
            return None
        sort_order = 'slug'
        if not current_slug:
            return random.choice(all_results)
        elif current_slug.isdigit():
            all_results = all_results.order_by(sort_order)
            return all_results[int(current_slug) % len(all_results)] # ignore direction: just provide a person
        else:
            all_results = all_results.exclude(slug=current_slug)
        if len(all_results) == 0: # special case: return the excluded person if they are the only one or nothing
            all_results = self.filter(can_be_featured=True)
            if all_results.exists():
                return all_results[0]
            else:
                return None
        if want_previous:
            sort_order = '-slug'
            results = all_results.order_by(sort_order).filter(slug__lt=current_slug)[:1]
        else:
            results = all_results.order_by(sort_order).filter(slug__gt=current_slug)[:1]
        if len(results) == 1:
            return results[0]
        else: # we're at the start/end of the list, wrap round to the other end
            results = all_results.order_by(sort_order)[:1]
            if len(results) == 1:
                return results[0]
            else:
                return None


class Person(ModelBase, HasImageMixin, ScorecardMixin, IdentifierMixin):
    title = models.CharField(max_length=100, blank=True)
    legal_name = models.CharField(max_length=300)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="auto-created from first name and last name",
        validators=[validate_person_slug],
    )
    gender = models.CharField(max_length=20, blank=True, help_text="this is typically, but not restricted to, 'male' or 'female'")
    date_of_birth = ApproximateDateField(blank=True, help_text=date_help_text)
    date_of_death = ApproximateDateField(blank=True, help_text=date_help_text)
    # religion
    # tribe
    summary = MarkupField(blank=True, default='')

    # The "primary" email address in some sense - there may be others
    # (or this one) in contacts.
    email = models.EmailField(blank=True)

    hidden = models.BooleanField(
        default=False,
        help_text="hide this person's pages from normal users")

    contacts = GenericRelation(Contact)
    identifiers = GenericRelation(Identifier)
    images = GenericRelation(Image)
    objects = PersonManager()

    can_be_featured = models.BooleanField(default=False, help_text="can this person be featured on the home page (e.g., is their data appropriate and extant)?")

    # Additional fields added largely for Popolo spec compliance:
    biography = MarkupField(blank=True, default='')
    national_identity = models.CharField(max_length=100, blank=True)
    family_name = models.CharField(max_length=300, blank=True)
    given_name = models.CharField(max_length=300, blank=True)
    additional_name = models.CharField(max_length=300, blank=True)
    honorific_prefix = models.CharField(max_length=300, blank=True)
    honorific_suffix = models.CharField(max_length=300, blank=True)
    sort_name = models.CharField(max_length=300, blank=True)

    fields_to_whitespace_normalize = ['title',
                                      'legal_name',
                                      'gender',
                                      'email',
                                      'national_identity',
                                      'family_name',
                                      'given_name',
                                      'additional_name',
                                      'honorific_prefix',
                                      'honorific_suffix',
                                      'sort_name']

    @property
    def name(self):
        # n.b. we're deliberately not using
        # self.alternative_names.filter(name_to_use=True) here, since
        # that would do a new query per person, even if the
        # alternative names had been loaded by prefetch_related.  See:
        #   http://stackoverflow.com/a/12974801/223092
        alternative_names_to_use = [an for an in self.alternative_names.all()
                                    if an.name_to_use]
        if alternative_names_to_use:
            return alternative_names_to_use[0].alternative_name
        else:
            return self.legal_name

    @property
    def everypolitician_uuid(self):
        return self.get_identifier('everypolitician')

    def additional_names(self, include_name_to_use=False):
        filter_args = {}
        if not include_name_to_use:
            filter_args['name_to_use'] = False
        return [an.alternative_name
                for an in
                self.alternative_names.filter(**filter_args)]

    def all_names_set(self):
        """Return a set of all known names for this Person"""
        result = set(self.additional_names(include_name_to_use=True))
        result.add(self.legal_name)
        return result

    @transaction.atomic
    def add_alternative_name(self, alternative_name, name_to_use=False, note=''):
        if name_to_use:
            # Make sure that no other alternative names are set as
            # the name to use:
            for an in self.alternative_names.all():
                an.name_to_use = False
                an.save()
        alternative_name = re.sub(r'\s+', ' ', alternative_name).strip()
        AlternativePersonName.objects.update_or_create({'person': self,
                                                        'alternative_name': alternative_name,
                                                        'note': note},
                                                       {'name_to_use': name_to_use})
        apn = AlternativePersonName(person=self,
                                    alternative_name=alternative_name,
                                    name_to_use=name_to_use)

    def remove_alternative_name(self, alternative_name):
        self.alternative_names.filter(alternative_name=alternative_name).delete()

    def aspirant_positions(self):
        return self.position_set.all().current_aspirant_positions()

    def aspirant_positions_ever(self):
        return self.position_set.all().aspirant_positions()

    def is_aspirant(self):
        return self.aspirant_positions().exists()

    def politician_positions(self):
        return self.position_set.all().current_politician_positions()

    def politician_positions_ever(self):
        return self.politician_positions()

    def is_politician(self):
        return self.politician_positions().exists()

    def parties(self):
        """Return list of parties that this person is currently a member of"""
        party_memberships = self.position_set.all().currently_active().filter(title__slug='member').filter(organisation__kind__slug='party')
        return Organisation.objects.filter(position__in=party_memberships)

    def parties_ever(self):
        """Return list of parties that this person has ever been a member of"""
        party_memberships = self.position_set.all().filter(title__slug='member').filter(organisation__kind__slug='party')
        return Organisation.objects.filter(position__in=party_memberships)

    def coalitions(self):
        """Return list of coalitions that this person is currently a member of"""
        coalition_memberships = self.position_set.all().currently_active().filter(title__slug='coalition-member')
        return Organisation.objects.filter(position__in=coalition_memberships)

    def parties_and_coalitions(self):
        """Return list of parties and coalitions that this person is currently a member of"""
        party_memberships = (
            self
            .position_set
            .all()
            .currently_active()
            .filter(
              # select the political party memberships
              ( Q(title__slug='member') & Q(organisation__kind__slug='party') )

              # select the coalition memberships
              | Q(title__slug='coalition-member')
            )
        )
        return Organisation.objects.filter(position__in=party_memberships).distinct()

    def constituencies(self):
        """Return list of constituencies that this person is currently an politician for"""
        return Place.objects.filter(position__in=self.politician_positions()).distinct()

    def constituency_offices(self):
        """
        Return list of constituency offices that this person is currently associated with.

        This is specific to the South African site (ZA).
        """
        contacts = self.position_set.filter(title__slug="constituency-contact").currently_active()
        return Organisation.objects.filter(position__in=contacts)

    def aspirant_constituencies(self):
        """Return list of constituencies that this person is currently an aspirant for"""
        return Place.objects.filter(position__in=self.aspirant_positions())

    def __unicode__(self):
        return self.legal_name

    @models.permalink
    def get_absolute_url(self):
        return ('person', [self.slug])

    def generate_tasks(self):
        """Generate tasks for missing contact details etc"""
        task_slugs = []

        wanted_contact_slugs = ['phone','email','address']
        have_contact_slugs = [c.kind.slug for c in self.contacts.all()]
        for wanted in wanted_contact_slugs:
            if wanted not in have_contact_slugs:
                task_slugs.append("find-missing-" + wanted)

        return task_slugs

    def scorecard_overall(self):
        total_count = super(Person, self).active_scorecards().count()
        total_score = super(Person, self).active_scorecards().aggregate(models.Sum('score'))['score__sum']

        for constituency in self.constituencies():
            constituency_count = constituency.active_scorecards().count()
            if constituency_count:
                total_count += constituency_count
                total_score += constituency.active_scorecards().aggregate(models.Sum('score'))['score__sum']

        return total_score / total_count

    def scorecards(self):
        """This is the list of scorecards that will actually be displayed on the site."""
        scorecard_lists = []

        # We're only showing scorecards for current MPs
        if self.is_politician():
            scorecard_lists.append(super(Person, self).scorecards())

            scorecard_lists.extend([x.scorecards() for x in self.constituencies()])

        return itertools.chain(*scorecard_lists)

    def has_scorecards(self):
        # We're only showing scorecards for current MPs
        if self.is_politician():
            return super(Person, self).has_scorecards() or any([x.has_scorecards() for x in self.constituencies()])

    @property
    def show_overall_score(self):
        """Should we show an overall score? Yes if applicable and there are active scorecards and we have the CDF category"""
        if super(Person, self).show_overall_score:
            # We could show the scorecard. Check that there is a CDF report in there.
            for constituency in self.constituencies():
                if constituency.active_scorecards().filter(category__slug='cdf-performance').exists():
                    return True

        # fall through to here
        return False

    class Meta:
       ordering = ["sort_name"]


def update_sort_name(**kwargs):
    """A signal handler function to set a default sort_name"""
    person = kwargs.get('instance')
    if person.legal_name and not person.sort_name:
        person.sort_name = person.legal_name.strip().split()[-1]

post_init.connect(update_sort_name, Person)


class AlternativePersonName(ModelBase):
    person = models.ForeignKey(Person, related_name='alternative_names')
    alternative_name = models.CharField(max_length=300)
    name_to_use = models.BooleanField(default=False)

    start_date = ApproximateDateField(blank=True, help_text=date_help_text)
    end_date = ApproximateDateField(blank=True, help_text=date_help_text)
    note = models.CharField(max_length=300, blank=True)

    family_name = models.CharField(max_length=300, blank=True)
    given_name = models.CharField(max_length=300, blank=True)
    additional_name = models.CharField(max_length=300, blank=True)
    honorific_prefix = models.CharField(max_length=300, blank=True)
    honorific_suffix = models.CharField(max_length=300, blank=True)

    fields_to_whitespace_normalize = ['alternative_name',
                                      'family_name',
                                      'given_name',
                                      'additional_name',
                                      'honorific_prefix',
                                      'honorific_suffix']

    objects = ManagerBase()

    def __unicode__(self):
        return self.alternative_name + (" [*]" if self.name_to_use else "")

    def get_admin_url(self):
        return False

    class Meta:
        unique_together = ("person", "alternative_name")


class OrganisationKind(ModelBase):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')

    fields_to_whitespace_normalize = ['name']

    objects = ManagerBase()

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]

    @models.permalink
    def get_absolute_url(self):
        return ('organisation_kind', (self.slug,))


class OrganisationQuerySet(models.query.GeoQuerySet):
    def parties(self):
        return self.filter(kind__slug='party')

    def active_parties(self):
        # FIXME - What a lot of subqueries...
        active_politician_positions = Position.objects.all().current_politician_positions()
        active_member_positions = Position.objects.all().filter(title__slug='member').currently_active()

        return (
            self
                .parties()
                .filter(
                    Q(position__in=active_politician_positions) |
                    Q(position__in=active_member_positions)
                )
                .distinct()
            )


class Organisation(ModelBase, HasImageMixin, IdentifierMixin):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200, editable=False)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="created from name",
        validators=[validate_organisation_slug],
    )
    summary = MarkupField(blank=True, default='')
    kind = models.ForeignKey('OrganisationKind')
    started = ApproximateDateField(blank=True, help_text=date_help_text)
    ended = ApproximateDateField(blank=True, help_text=date_help_text)

    seats = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="The number of seats this organisation nominally has."
    )

    show_attendance = models.BooleanField(
        default=False,
        help_text="Toggles attendance records on person detail pages for people who belong to this organization.")

    fields_to_whitespace_normalize = ['name']

    objects = OrganisationQuerySet.as_manager()
    contacts = GenericRelation(Contact)
    identifiers = GenericRelation(Identifier)
    images = GenericRelation(Image)
    informationsources = GenericRelation(InformationSource)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.kind)

    @models.permalink
    def get_absolute_url(self):
        return ('organisation', [self.slug])

    class Meta:
       ordering = ["name"]

    def is_ongoing(self):
        """Return True or False for whether the organisation is currently ongoing"""
        if not self.ended:
            return True
        elif self.ended.future:
            return True
        else:
            # turn today's date into an ApproximateDate object and cmp to that
            now = datetime.date.today()
            now_approx = ApproximateDate(year=now.year, month=now.month, day=now.day)
            return now_approx <= self.ended

    def __shorten_name(self):

        name = self.name

        strip_phrases = [
            'Portfolio Committee on',
            'Standing Committee on',
        ]

        for phrase in strip_phrases:
            name = re.sub('(?i)' + re.escape(phrase), '', name)

        return name.strip()

    def save(self, *args, **kwargs):
        self.short_name = self.__shorten_name()
        super(Organisation, self).save(*args, **kwargs)


class PlaceKind(ModelBase):
    name = models.CharField(max_length=200, unique=True)
    plural_name = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')

    fields_to_whitespace_normalize = ['name', 'plural_name']

    objects = ManagerBase()

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["slug"]

    def parliamentary_sessions(self):
        """Return a list of any associated parliamentary sessions"""

        return ParliamentarySession.objects.filter(place__kind=self).distinct()

    def parliamentary_sessions_for_iteration(self):
        """Return a list of associated parliamentary sessions for iteration

        If there are no parliamentary_sessions associated with this
        PlaceKind (e.g. as with Country) then rather than returning a
        empty list, return [None].  This makes iterating over sessions
        in templates much simpler."""

        sessions = self.parliamentary_sessions()
        if sessions.count() == 0:
            return [None]
        else:
            return sessions


class PlaceQuerySet(models.query.GeoQuerySet):
    def constituencies(self):
        return self.filter(kind__slug='constituency')

    def counties(self):
        return self.filter(kind__slug='county')

    def order_by_parliamentary_session(self):
        """This is a helper for use in the place_places.html template"""
        return self.order_by('-parliamentary_session__start_date', 'name')

    def order_by_kind(self):
        """This is a helper for use in the place_places.html template"""
        return self.order_by('-kind__name', 'name')


class Place(ModelBase, HasImageMixin, ScorecardMixin, BudgetsMixin, IdentifierMixin):
    name = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="created from name",
        validators=[validate_place_slug],
    )
    kind = models.ForeignKey('PlaceKind')
    summary = MarkupField(blank=True, default='')
    shape_url = models.URLField(blank=True)
    location = models.PointField(null=True, blank=True)
    organisation = models.ForeignKey('Organisation', null=True, blank=True, help_text="use if the place uniquely belongs to an organisation - eg a field office" )
    parliamentary_session = models.ForeignKey('ParliamentarySession', null=True, blank=True)

    mapit_area = models.ForeignKey( mapit_models.Area, null=True, blank=True )
    parent_place = models.ForeignKey('self', blank=True, null=True, related_name='child_places')

    fields_to_whitespace_normalize = ['name']

    identifiers = GenericRelation(Identifier)
    images = GenericRelation(Image)

    objects = PlaceQuerySet.as_manager()
    is_overall_scorecard_score_applicable = False

    @property
    def position_with_organisation_set(self):
        return self.position_set.filter(organisation__isnull=False)

    @property
    def extra_autocomplete_data(self):
        return self.kind.name

    def __unicode__(self):
        session_suffix = ""
        if self.parliamentary_session:
            session_suffix += " " + str(self.parliamentary_session.short_date_range())
        return "%s (%s%s)" % (self.name, self.kind, session_suffix)

    def is_constituency(self):
        return self.kind.slug == 'constituency'

    def current_politician_position(self):
        """Return the current politician position, or None.

        FIXME - This just returns a random position from what could be a set.
        """
        qs = self.position_set.all().current_politician_positions()
        try:
            return qs[0]
        except IndexError:
            return None

    def related_people(self, positions_filter=significant_positions_filter):
        """Find significant people associated with this place"""

        positions = Position.objects.filter(
            place=self,
            person__hidden=False,
        ).currently_active()
        positions = positions_filter(positions)

        # Group all the positions by person:
        result_dict = defaultdict(list)
        for position in positions:
            result_dict[position.person].append(position)
        # Sort each list of positions ordered with the latest ending
        # positions first:
        for position_list in result_dict.values():
            position_list.sort(key=lambda p: p.sorting_end_date_high,
                               reverse=True)
        # Order the people by last name:
        return sorted(result_dict.items(),
                      key=lambda t: t[0].sort_name)

    def related_people_child_places(self, positions_filter=significant_positions_filter):
        """Find significant people associated with child places"""

        results = []
        for child_place in self.child_places.all():
            people_and_positions = child_place.related_people(positions_filter)
            if people_and_positions:
                results.append((child_place, people_and_positions))
        return results

    def parent_places(self):
        """Return an array of all the parent places."""
        if self.parent_place:
            parents = [ self.parent_place ]
            parents.extend( self.parent_place.parent_places() )
            # print parents
            return parents
        else:
            return []

    def self_and_parents(self):
        """Return a query set that matches this place and all parents."""
        parents = self.parent_places()
        ids     = [ x.id for x in parents ]
        ids.append(self.id)
        return Place.objects.filter(pk__in=ids)


    def all_related_positions(self):
        """Return a query set of all the positions for this place, and all parent places."""
        return Position.objects.filter(place__in=self.self_and_parents())

    def all_related_politicians(self):
        """Return a query set of all the politicians for this place, and all parent places."""
        return Person.objects.filter(position__in=self.all_related_positions().politician_positions()).distinct()

    def all_related_current_politicians(self):
        """Return a query set of all the current politicians for this place, and all parent places."""
        positions = self.all_related_positions().current_politician_positions()
        return Person.objects.filter(position__in=positions).distinct()

    def child_places_by_kind(self):
        """Return all concurrent child places, grouped by their PlaceKind

        By 'concurrent child places', we mean either those where their
        parliamentary sessions overlap, or where either this place or
        the child place isn't associated with a parliamentary session."""

        results = defaultdict(list)
        for p in self.child_places.all():
            if self.parliamentary_session and p.parliamentary_session:
                if self.parliamentary_session.overlaps(p.parliamentary_session):
                    results[p.kind].append(p)
            else:
                results[p.kind].append(p)
        for v in results.values():
            v.sort(key=lambda e: e.name)
        return dict(results)

    @models.permalink
    def get_absolute_url(self):
        return ('place', [self.slug])

    class Meta:
       ordering = ["slug"]

    def get_boundary_changes(self):
        """Return a dictionary representing previous and next boundary changes

        A dictionary with the keys 'previous' and 'next' either mapping
        to null (if there is no boundary data in the previous / next
        parliamentary session for this PlaceKind) or a dictionary with
        details about the Places that this boundary overlapped with in
        that session.  For example, it might return:

        {'previous': {'session': ParliamentarySession(...),
                      'connector': 'was in',
                      'intersections': [{'percent': 92.5,
                                         'place': Place(...)},
                                        {'percent': 7.5,
                                         'place': Place(...)}],
                      'cutoff': 1,
                      'others': [Place(...), Place(...)]}
         'next': None}
        """

        # This is the percentage overlap below which we just list the
        # area name in a note below the main changes:
        cutoff = 1

        previous_sessions = []
        next_sessions = []
        append_to = previous_sessions
        for session in self.kind.parliamentary_sessions():
            if session == self.parliamentary_session:
                append_to = next_sessions
                continue
            append_to.append(session)

        previous_session = previous_sessions[-1] if previous_sessions else None
        next_session = next_sessions[0] if next_sessions else None

        connectors = {'previous': {'Past': 'was previously in',
                                   'Current': 'is currently in',
                                   'Future': 'will be in'},
                      'next': {'Past': 'was subsequently in',
                               'Current': 'is currently in',
                               'Future': 'will be in'}}

        result = {}

        # Occasionally a place will not have a MapIt area associated
        # with it; in these cases we can't find which boundaries it
        # overlaps with, so just return an empty dictionary.
        if self.mapit_area is None:
            return result

        for key, session in (('previous', previous_session),
                             ('next', next_session)):
            if not session:
                result[key] = None
                continue
            intersections = []
            for area in mapit_models.Area.objects.intersect('intersects',
                                               self.mapit_area,
                                               [self.mapit_area.type.code],
                                               mapit_models.Generation.objects.get(pk=session.mapit_generation)):
                # Now work out the % intersection between the two:
                self_geos_geometry = self.mapit_area.polygons.collect()
                if self_geos_geometry.area == 0:
                    continue
                other_geos_geometry = area.polygons.collect()
                intersection = self_geos_geometry.intersection(other_geos_geometry)
                proportion_shared = intersection.area / self_geos_geometry.area
                intersections.append((100 * proportion_shared,
                                      Place.objects.get(kind=self.kind,
                                                        parliamentary_session=session,
                                                        mapit_area=area)))
            intersections.sort(key=lambda x: -x[0])
            result[key] = {'session': session,
                           'connector': connectors[key][session.relative_time()],
                           'intersections': [{'percent': i[0],
                                              'place': i[1]} for i in intersections if i[0] >= cutoff],
                           'cutoff': cutoff,
                           'others': sorted([i[1] for i in intersections if i[0] < cutoff],
                                            key=lambda x: x.name)}

        return result

    def get_aspirants(self):
        """Return aspirants for this place and each parent place

        This returns, for this page and each larger parent place
        recursively, all the current aspirants for positions that
        reference that place.  The intention is that this provides a
        data structure that is easily consumable by templates.  For
        example, for the 2013 Constituency Ainabkoi, this might
        return:

           [(<Place: Ainabkoi (Constituency 2013-)>, {}),
            (<Place: Uasin Gishu (County 2013-)>,
             {u'Aspirant Governor': [<Person: Margaret Jepkoech Kamar >],
              u'Aspirant Senator': [<Person: Abraham Kiptanui>]}),
            (<Place: Rift Valley (Province)>, {}),
            (<Place: Kenya (Country)>,
             {u'Aspirant President': [<Person: David Gian Maillu>,
               <Person: Peter Kenneth>,
               <Person: Uhuru Muigai Kenyatta>,
               <Person: Martha Wangari Karua>,
               <Person: Paul Kibugi Muite>]})]

        (Note that this example was based on incomplete test data.)"""

        found_any_aspirants = False

        # This is a classically horrible thing to try to do with SQL -
        # recurse up this place's hierarchy via the parent column -
        # however, we know that there will only be at most 5 levels
        # (Ward -> Constituency -> County -> Province -> Country) for
        # Kenya, and the results of the query should be cached.

        place_hierarchy = []

        current_place = self
        while True:
            place_hierarchy.append(current_place)
            parent = current_place.parent_place
            current_place_session = current_place.parliamentary_session
            if parent:
                # If the parent place is actually from a non-overlapping
                # parliamentary sessions, stop recursing:
                parent_session = parent.parliamentary_session
                if parent_session and current_place_session:
                    if not parent_session.overlaps(current_place_session):
                        break
                current_place = parent
            else:
                break

        # Preserve the order of places in the hierarchy, but allow
        # fast lookups with a dict:
        place_to_index = dict((p, i) for i, p in enumerate(place_hierarchy))

        aspirants_for_places = [(p, defaultdict(list)) for p in place_hierarchy]

        for position in Position.objects.filter(place__in=place_hierarchy, title__slug__startswith='aspirant-').currently_active():
            found_any_aspirants = True
            aspirants_for_places[place_to_index[position.place]][1][position.title.name].append(position.person)

        # Annoyingly, defaultdicts can't be easily be iterated over in
        # Django templates, since some_defaultdict.items first tries
        # to access some_defaultdict['items'] which returns an empty
        # list.  A workaround is to convert to a dictionary instead.
        # See http://stackoverflow.com/q/4764110/223092

        if found_any_aspirants:
            return [(p, dict(dd)) for p, dd in aspirants_for_places]
        else:
            return None

    @property
    def show_active(self):
        if self.parliamentary_session:
            return self.parliamentary_session.end_date >= datetime.date.today()
        else:
            True

class PositionTitle(ModelBase):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    responsibilities = MarkupField(blank=True, default='')
    requires_place = models.BooleanField(default=False, help_text="Does this job title require a place to complete the position?")

    fields_to_whitespace_normalize = ['name']

    objects = ManagerBase()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('position_pt', [self.slug])

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
                .annotate(position_count=models.Count('position'))
                .order_by('-position_count')
        )

        return orgs


    class Meta:
       ordering = ["slug"]


class PositionQuerySet(models.query.GeoQuerySet):
    def currently_active(self, when=None):
        """Filter on start and end dates to limit to currently active positions"""

        if when == None:
            when = datetime.date.today()

        now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))

        qs = (
            self
                .filter(sorting_start_date__lte=now_approx)
                .filter(Q(sorting_end_date_high__gte=now_approx) | Q(end_date=''))
        )

        return qs

    def currently_inactive(self, when=None):
        """Filter on start and end dates to limit to currently inactive positions"""

        if when == None:
            when = datetime.date.today()

        now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))

        start_criteria = Q(start_date__gt=now_approx)
        end_criteria = Q(sorting_end_date_high__lt=now_approx) & ~Q(end_date='')

        qs = self.filter(start_criteria | end_criteria)

        return qs

    def previous(self, when=None):
        """Filter end dates to limit to positions which are already over."""

        when = when or datetime.date.today()

        when_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))

        end_criteria = Q(sorting_end_date_high__lt=when_approx) & ~Q(end_date='')

        return self.filter(end_criteria)

    def future(self, when=None):
        """Positions which have not yet started."""

        when = when or datetime.date.today()

        when_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))

        start_criteria = Q(sorting_start_date__gt=when_approx)

        return self.filter(start_criteria)

    def overlapping_dates(self, start_date, end_date):
        start_criteria = \
            Q(start_date='') | \
            Q(start_date='past') | \
            Q(sorting_start_date__lte=end_date)
        end_criteria = \
            Q(end_date='') | \
            Q(end_date='future') | \
            Q(sorting_end_date_high__gte=start_date)
        return self.filter(start_criteria & end_criteria)

    def aspirant_positions(self):
        """
        Filter down to only positions which are aspirant ones. This uses the
        convention that the slugs always start with 'aspirant-'.
        """
        return self.filter( title__slug__startswith='aspirant-' )

    def current_aspirant_positions(self, when=None):
        """Filter down to only positions which are those of current aspirants."""
        return self.aspirant_positions().currently_active(when)

    def current_politician_positions(self, when=None):
        """Filter down to only positions which are those of current politicians."""
        return self.political().currently_active(when)

    def political(self):
        """Filter down to only the political category"""
        return self.filter(category='political')

    def committees(self):
        """Filter down to committee memberships"""
        return self.filter(organisation__slug__contains='committee') \
            .order_by('-end_date', '-start_date')

    def exclude_committees(self):
        return self.exclude(organisation__slug__contains='committee')

    def education(self):
        """Filter down to only the education category"""
        return self.filter(category='education')

    def other(self):
        """Filter down to only the other category"""
        return self.filter(category='other')

    def order_by_place(self):
        """Sort by the place name"""
        return self.order_by('place__name')

    def order_by_person_name(self):
        """Sort by the place name"""
        return self.order_by('person__sort_name')

    def current_unique_places(self):
        """Return the list of places associated with current positions"""
        result = sorted(set(position.place for position in self.currently_active()
                          if position.place),
                      key=lambda p: p.name)
        return result

    def person_sort_name_prefix(self, prefix):
        """Filter by a prefix of the person's sort_name"""
        return self.filter(person__sort_name__istartswith=prefix)

    def active_at_end_of_year(self, year):
        """Return the active positions at the of year, or today if it's before."""
        last_day = get_latest_day_of_year(year)
        return self.currently_active(last_day)

    def active_during_year(self, year):
        """
        Return the positions that were active for a period during,
        or at the end of the year.
        """
        first_day = datetime.date(year, 1, 1)
        last_day = get_latest_day_of_year(year)
        return self.overlapping_dates(first_day, last_day)

    def title_slug_prefixes(self, titles):
        """Fileter positions by prefixes in the title's slug"""
        qs = [Q(title__slug__startswith=title) for title in titles]
        return self.filter(reduce(lambda acc, item: acc | item, qs))

class Position(ModelBase, IdentifierMixin):
    category_choices = (
        ('political', 'Political'),
        ('education', 'Education (as a learner)'),
        ('other', 'Anything else'),
    )

    person = models.ForeignKey('Person')
    organisation = models.ForeignKey('Organisation', null=True, blank=True)
    place = models.ForeignKey('Place', null=True, blank=True, help_text="use if needed to identify the position - eg add constituency for a politician" )
    title = models.ForeignKey('PositionTitle', null=True, blank=True)
    subtitle = models.CharField(max_length=200, blank=True, default='')
    category = models.CharField(max_length=20, choices=category_choices, default='other', help_text="What sort of position was this?")
    note = models.CharField(max_length=300, blank=True, default='')

    start_date = ApproximateDateField(blank=True, help_text=date_help_text)
    end_date = ApproximateDateField(blank=True, help_text=date_help_text, default="future")

    # hidden fields that are only used to do sorting. Filled in by code.
    #
    # These sort dates are here to enable the expected sorting. Ascending is
    # quite straight forward as the string stored (eg '2011-03-00') will sort as
    # expected. But for descending sorts they will not, as '2011-03-00' would
    # come after '2011-03-15'. To fix this the *_high dates below replace '00'
    # with '99' so that the desc sort can be carried out in SQL as expected.
    #
    # For 'future' dates there are also some special tweaks that makes them sort
    # as expeced. See the '_set_sorting_dates' method below for implementation.
    #
    sorting_start_date = models.CharField(editable=True, default='', max_length=10)
    sorting_end_date = models.CharField(editable=True, default='', max_length=10)
    sorting_start_date_high = models.CharField(editable=True, default='', max_length=10)
    sorting_end_date_high = models.CharField(editable=True, default='', max_length=10)

    identifiers = GenericRelation(Identifier)

    objects = PositionQuerySet.as_manager()

    def clean(self):
        if not (self.organisation or self.title or self.place):
            raise exceptions.ValidationError('Must have at least one of organisation, title or place.')

        if self.title and self.title.requires_place and not self.place:
            raise exceptions.ValidationError("The job title '%s' requires a place to be set" % self.title.name)


    def display_dates(self):
        """
        Return nice HTML for the display of dates.

        This has become a twisty maze of conditionals :( - note that there are
        extensive tests for the various possible outputs.
        """

        # used in comparisons in the conditionals below
        approx_past   = ApproximateDate(past=True)
        today         = datetime.date.today()
        approx_today  = ApproximateDate(year=today.year, month=today.month, day=today.day)
        approx_future = ApproximateDate(future=True)

        # no dates
        if not (self.start_date or self.end_date):
            return ''

        # start but no end
        elif not self.end_date or self.end_date == approx_past:
            message = ''
            if not self.start_date:
                message = "Ended" # end_date is past
            elif self.start_date == approx_future:
                message = "Not started yet"
            elif self.start_date == approx_past:
                message = "Started"
            elif self.start_date <= approx_today:
                message = "Started %s" % self.start_date
            else:
                message = "Will start %s" % self.start_date

            if self.end_date == approx_past:
                if not self.start_date or self.start_date == approx_past or self.start_date == approx_future:
                    message = "Ended"
                else:
                    message += ", now ended"

            return message

        # end but no start
        elif not self.start_date or self.start_date == approx_past:
            if not self.end_date or self.end_date == approx_past:
                return "Ended"
            elif self.end_date == approx_future:
                return "Ongoing"
            elif self.end_date < approx_today:
                return "Ended %s" % self.end_date
            else:
                return "Will end %s" % self.end_date

        # both dates
        else:
            if self.end_date == approx_future:
                if self.start_date == approx_future:
                    return "Not started yet"
                elif self.start_date <= approx_today:
                    return "Started %s" % self.start_date
                else:
                    return "Will start %s" % self.start_date
            elif self.start_date == approx_future:
                if self.end_date < approx_today:
                    return "Ended %s" % self.end_date
                else:
                    return "Will end %s" % self.end_date
            else:
                return "%s &rarr; %s" % (self.start_date, self.end_date)

    def approximate_date_overlap(self, start_date, end_date):
        """Return the approximate overlap between this position and a date range

        This may be *very* approximate, but it's sometimes useful to
        be able to have a rough idea of how much a position overlaps
        with a date range, e.g. to see which parliamentary term a
        position is most likely to refer to.

        This returns a datetime.timedelta object.
        """
        approx_start = approximate_date_to_date(self.start_date, 'earliest')
        approx_end = approximate_date_to_date(self.end_date, 'latest')
        latest_start = max(approx_start, start_date)
        earliest_end = max(approx_end, end_date)
        if earliest_end <= latest_start:
            return datetime.timedelta(days=0)
        return earliest_end - latest_start

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
            now_approx = ApproximateDate(year=now.year, month=now.month, day=now.day)
            return now_approx <= self.end_date

    def is_active_at_date(self, date):
        """
        Return True if this position was active on a specific date.
        Date is in format 'yyyy-mm'dd'
        """
        if self.start_date:
            if date >= self.sorting_start_date or self.start_date == '' or self.start_date == 'past':
                if date <= self.sorting_end_date_high or self.end_date == '' or self.end_date == 'future':
                    return True
        return False

    def has_known_dates(self):
        """Is there at least one known (not future) date?"""
        return (self.start_date and not self.start_date.future) or (self.end_date and not self.end_date.future)

    def _set_sorting_dates(self):
        """Set the sorting dates from the actual dates (does not call save())"""

        past_repr = '0001-00-00'
        none_repr = '0000-00-00'

        # value can be yyyy-mm-dd, future or None
        start = repr(self.start_date) if self.start_date else None
        end   = repr(self.end_date)   if self.end_date   else None

        # set the value or default to something sane
        sorting_start_date =        start or none_repr
        sorting_end_date   = end or start or none_repr
        if not end and start == 'past': sorting_end_date = none_repr

        # chaange entries to have the past_repr
        if start              == 'past': start              = past_repr
        if end                == 'past': end                = past_repr
        if sorting_start_date == 'past': sorting_start_date = past_repr
        if sorting_end_date   == 'past': sorting_end_date   = past_repr

        # To make the sorting consistent special case some parts
        if not end and start == 'future':
            sorting_start_date = 'a-future' # come after 'future'

        self.sorting_start_date = sorting_start_date
        self.sorting_end_date   = sorting_end_date

        self.sorting_start_date_high = re.sub('-00', '-99', sorting_start_date)
        self.sorting_end_date_high   = re.sub('-00', '-99', sorting_end_date)

    def is_nominated_politician(self):
        return self.title.slug == 'nominated-member-parliament'

    def save(self, *args, **kwargs):
        self._set_sorting_dates()
        super(Position, self).save(*args, **kwargs)

    def __unicode__(self):
        title = self.title or '???'

        if self.organisation:
            organisation = self.organisation.name
        else:
            organisation = '???'

        return "%s (%s at %s)" % ( self.person.legal_name, title, organisation)

    class Meta:
        ordering = ['-sorting_end_date', '-sorting_start_date']

class ParliamentarySession(ModelBase):
    start_date = DateField(blank=True, null=True)
    end_date = DateField(blank=True, null=True)
    house = models.ForeignKey('Organisation', blank=True, null=True)
    position_title = models.ForeignKey('PositionTitle', blank=True, null=True)
    # It's not clear whether this field is a good idea or not - it
    # suggests that boundaries won't change within a
    # ParliamentarySession.  This assumption might well be untrue.
    # FIXME: in any case, this should just be a foreign key to Generation, surely...
    mapit_generation = models.PositiveIntegerField(blank=True,
                                                   null=True,
                                                   help_text='The MapIt generation with boundaries for this session')
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="specify manually")

    fields_to_whitespace_normalize = ['name']

    def __repr__(self):
        return "<ParliamentarySession: %s>" % (self.name,)

    def __unicode__(self):
        return unicode(self.name)

    def covers_date(self, d):
        return (d >= self.start_date) and (d <= self.end_date)

    def relative_time(self):
        today = datetime.date.today()
        if today > self.end_date:
            return "Past"
        elif today < self.start_date:
            return "Future"
        elif self.covers_date(today):
            return "Current"

    def overlaps(self, other):
        return self.start_date <= other.end_date and other.start_date <= self.end_date

    def short_date_range(self):
        if self.end_date and self.end_date.year != 9999:
            return "%s-%s" % (self.start_date.year, self.end_date.year)
        else:
            return "%s-" % (self.start_date.year,)

    @staticmethod
    def format_date(d):
        df = DateFormat(d)
        return df.format('jS F Y')

    def readable_date_range(self):
        future_sentinel = datetime.date(9999, 12, 31)
        if self.end_date == future_sentinel:
            return "from %s onwards" % (self.format_date(self.start_date),)
        else:
            return "from %s to %s" % (self.format_date(self.start_date),
                                      self.format_date(self.end_date))

    def positions_url(self):
        if not self.position_title:
            msg = ("There are currently no position views that don't require "
                   " a position title")
            raise NotImplementedError(msg)
        if not self.house:
            return reverse('position_pt', kwargs={
                'pt_slug': self.position_title.slug
            })
        return reverse('position_pt_ok_o', kwargs={
            'pt_slug': self.position_title.slug,
            'ok_slug': self.house.kind.slug,
            'o_slug': self.house.slug,
        })

    class Meta:
        ordering = ['start_date']


class OrganisationRelationshipKind(ModelBase):
    """This represent a kind of relationship two organisations can be in

    For example (a) this might be "has_office" for:

       party_a "has_office" constituency_office_42

    For example (b) "is_in_coalition" for:

       party_b "is_in_coalition" huge_coalition

    This is deliberately kept quite minimal for this first
    implementation, just using a relation name for a directed link
    between the two organisations.  This potentially could also
    include:
      - The allowed OrganisationKind of each Organisation
      - Start and end dates of the relationship
    """
    name = models.CharField(max_length=200, unique=True)

    fields_to_whitespace_normalize = ['name']


class OrganisationRelationship(ModelBase):
    """Represents a relationship between two organisations"""
    organisation_a = models.ForeignKey(Organisation, related_name='org_rels_as_a')
    organisation_b = models.ForeignKey(Organisation, related_name='org_rels_as_b')
    kind = models.ForeignKey(OrganisationRelationshipKind)


def raw_query_with_prefetch(query_model, query, params, fields_prefetches):
    """A workaround not being able to do select_related on a RawQuerySet

    Sometimes you may need to run a query that can't be expressed in
    Django's ORM without using a RawQuerySet.  Unfortunately, you
    can't use select_related on a RawQuerySet.  This wrapper for
    Manager's raw method will do the raw query, then run a single
    extra query (as prefetch_related does) for each of the ForeignKey
    fields in fields_prefetches (those that we would want to do
    select_related on) and fills in those fields on each of the
    objects found from the raw query.  If the second element of each
    tuple in fields_prefetches is a non-empty sequence, then those
    fields on the related model will be prefetched as well.

    Example:

        all_positions = raw_query_with_prefetch(
            models.Position,
            'SELECT * FROM core_position WHERE ....',
            (), # Any parameters for the raw query
            (('person', ('alternative_names', 'images')),
             ('organisation', ()))
        )
    """

    # We need to iterate over every object repeatedly anyway, so
    # evaluate the RawQuerySet at the start:
    objects = list(query_model.objects.raw(query, params=params))
    fields = [f for f, _ in fields_prefetches]
    # Check that each field is really a ForeignKey, and get the mode it refers to:
    name_to_field = {
        f.name: f.rel.to for f in query_model._meta.fields
        if f.get_internal_type() == 'ForeignKey'
    }
    for f in fields:
        if f not in name_to_field:
            raise Exception, "{0} was not a ForeignKey field".format(f)
    # Find all IDs for each field:
    field_ids = defaultdict(set)
    for o in objects:
        for field in fields:
            related_id = getattr(o, field + '_id')
            if related_id:
                field_ids[field].add(related_id)
    # For each field get all the objects with IDs that we just found,
    # and set them on each of the original objects:
    for field, prefetches in fields_prefetches:
        field_id = field + '_id'
        related_objects = name_to_field[field].objects.filter(
            pk__in=field_ids[field]
        )
        if prefetches:
            related_objects = related_objects.prefetch_related(*prefetches)
        object_id_to_object = {o.id: o for o in related_objects}
        for o in objects:
            related_object = object_id_to_object.get(getattr(o, field_id))
            if related_object:
                setattr(o, field, related_object)
    return objects
