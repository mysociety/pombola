# This is needed to avoid an error that there's "no module named
# models" when importing Identifier from popolo.models.
# This was caused because the import mechanism tries the popolo module
# in this same package first.  By forcing only absolute imports, this
# will get the django-popolo package's popolo package instead.
from __future__ import absolute_import

import time
import calendar
import datetime
import os
import random
import json
import string
import sys
import subprocess
import unicodecsv as csv
from urlparse import urlsplit, urlunsplit, urljoin
from os.path import dirname

import django
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.views.decorators.cache import cache_control, never_cache
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View

from popolo.models import Identifier
from slug_helpers.views import SlugRedirectMixin, get_slug_redirect

from pombola.core import models
from pombola.country import override_current_session


class HomeView(TemplateView):

    template_name = 'home.html'

    def get_context_data(self, **kwargs):

        context = super(HomeView, self).get_context_data(**kwargs)

        before, after = (self.request.GET.get(k) for k in ('before', 'after'))
        current_slug = before or after

        context['featured_person'] = \
            models.Person.objects.get_next_featured(current_slug,
                                                    want_previous=before)

        # For the election homepage produce a list of all the featured people.
        # Shuffle it each time to avoid any bias.
        context['featured_persons'] = list(models.Person.objects.get_featured())
        random.shuffle(context['featured_persons'])

        return context

class HelpApiView(TemplateView):

    template_name = 'core/help_api.html'

    def get_context_data(self, **kwargs):
        context = super(HelpApiView, self).get_context_data(**kwargs)
        # Generate the links to the PopIt API endpoint and the
        # prettier web interface:
        split_url = list(urlsplit(settings.POPIT_API_URL))
        context['popit_api_url'] = urlunsplit(split_url)
        # Remove the path and any query string:
        for i in range(2, len(split_url)):
            split_url[i] = ''
        context['popit_url'] = urlunsplit(split_url)
        # Set the URL path to the nightly JSON exports:
        context['postgresql_dump_base_path'] = settings.MEDIA_URL + 'dumps/'
        context['popolo_dump_base_path'] = settings.MEDIA_URL + 'popolo_json/'
        return context


class OrganisationList(ListView):
    model = models.Organisation


class SkipHidden(object):

    def get_queryset(self):
        qs = super(SkipHidden, self).get_queryset()
        # Only display person pages for hidden people if the user is
        # logged in and a superuser:
        if self.request.user.is_superuser:
            return qs
        return qs.filter(hidden=False)


class CommentArchiveMixin(object):
    """This checks whether the current page has a matching Disqus
       comment thread in the local /data/disqus.json file, which is a frozen
       copy of the output of an non-admin call to the Disqus API at
       https://disqus.com/api/3.0/forums/listPosts.json?forum=<DISQUS_SHORTNAME>&order=desc&related=thread&limit=100"""

    def check_for_archive_link(self, path):
        if settings.COUNTRY_APP == None:
            return

        try:
            archive_file = os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    os.pardir,
                    settings.COUNTRY_APP,
                    'data/disqus.json',
                    )
                )
            with open(archive_file) as f:
                archives = json.load(f)
        except IOError:
            return
        for archive in archives['response']:
            disqus_thread_link = archive['thread']['link']
            if urlsplit(disqus_thread_link).path == path:
                return disqus_thread_link

    def get_context_data(self, **kwargs):
        context = super(CommentArchiveMixin, self).get_context_data(**kwargs)
        if settings.FACEBOOK_APP_ID:
            context['archive_link'] = self.check_for_archive_link(self.request.path)
        return context


class SubSlugRedirectMixin(SlugRedirectMixin):
    """This customization of SlugRedirectMixin understands sub pages"""

    def object_to_detail_url_pattern_name(self, o):
        url_pattern_name = o.__class__.__name__.lower()
        try:
            url_pattern_name += '_' + self.sub_page
        except AttributeError:
            pass
        return url_pattern_name

    def redirect_to(self, correct_object):
        pattern = self.object_to_detail_url_pattern_name(correct_object)
        url = reverse(pattern, args=[correct_object.slug])
        return redirect(url)


class BaseDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super(BaseDetailView, self).get_context_data(**kwargs)
        context.update(self.object.get_disqus_thread_data(self.request))
        return context


class BasePersonDetailView(SkipHidden, BaseDetailView):
    model = models.Person

    def get_context_data(self, **kwargs):
        context = super(BasePersonDetailView, self).get_context_data(**kwargs)
        if settings.ENABLED_FEATURES['hansard']:
            hansard_count = self.object.hansard_entries.count()
            if hansard_count:
                context['appearances_sub_link_text'] = \
                    'Appearances ({number_of_appearances})'.format(
                        number_of_appearances=hansard_count
                    )
            else:
                context['appearances_sub_link_text'] = 'Appearances'
        return context

    pass


class PersonDetail(SlugRedirectMixin, BasePersonDetailView):
    pass


class PersonDetailSub(SubSlugRedirectMixin, BasePersonDetailView):
    sub_page = None

    def get_template_names(self):
        return ["core/person_%s.html" % self.sub_page]

class PersonSpeakerMappingsMixin(object):
    def pombola_person_to_sayit_speaker(self, person):
        try:
            return person.sayit_link.sayit_speaker
        except ObjectDoesNotExist:
            return None


class BasePlaceDetailView(BaseDetailView):
    model = models.Place

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BasePlaceDetailView, self).get_context_data(**kwargs)
        context['place_type_count'] = models.Place.objects.filter(kind=self.object.kind).count()
        context['related_people'] = self.object.related_people()
        if settings.ENABLED_FEATURES['projects']:
            # The number of projects associated with the place is used
            # in the link text in the object_menu_links:
            context['projects_sub_link_text'] = \
                'CDF Projects ({number_of_projects})'.format(
                    number_of_projects=self.object.project_set.count()
                )
        return context


class PlaceDetailView(SlugRedirectMixin, BasePlaceDetailView):
    pass


class PlaceDetailSub(SubSlugRedirectMixin, BasePlaceDetailView):
    model = models.Place
    child_place_grouper = 'parliamentary_session'
    sub_page = None

    def get_context_data(self, **kwargs):
        context = super(PlaceDetailSub, self).get_context_data(**kwargs)
        context['child_place_grouper'] = self.child_place_grouper
        return context

    def get_template_names(self):
        return ["core/place_%s.html" % self.sub_page]

class PlaceKindList(ListView):
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        session_slug = self.kwargs.get('session_slug')

        if slug and slug != 'all':
            self.kind = get_object_or_404(
                models.PlaceKind,
                slug=slug
            )
            queryset = self.kind.place_set.all()
        else:
            self.kind = None
            queryset = models.Place.objects.all()

        if session_slug:
            self.session = get_object_or_404(
                models.ParliamentarySession,
                slug=session_slug
            )
        else:
            self.session = None

        # If this is a PlaceKind with parliamentary sessions, but a
        # particular one hasn't been specified, make the default either
        # the current session, or the most recent one if there is no
        # current session.  (This is largely to make any old bookmarked
        # links to (e.g.) /place/is/constituency/ still work.)

        if self.kind and not self.session:
            sessions = list(self.kind.parliamentary_sessions())
            if sessions:
                today = datetime.date.today()
                current_sessions = [s for s in sessions if s.covers_date(today)]
                if current_sessions:
                    self.session = current_sessions[0]
                else:
                    self.session = sessions[-1]

        if queryset and self.session:
            queryset = queryset.filter(parliamentary_session=self.session)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(PlaceKindList, self).get_context_data(**kwargs)
        context.update(
            kind = self.kind,
            selected_session = self.session,
            all_kinds = models.PlaceKind.objects.all(),
        )
        return context


def positions_count_for_letter(positions):
    """Count positions by inital letter of the holders' names

    Given a queryset of positions, this will return a list of tuples
    where each is (letter, position_count); this groups together and
    counts the positions held by people whose sort_name has the same
    initial letter.
    """
    return [
        (letter, positions.person_sort_name_prefix(letter).count())
        for letter in string.ascii_uppercase
    ]


def filter_by_alphabet(prefix_letter, position_qs):
    """A helper for producing an alpabetic grouping of positions

    We sometimes wish to list the people holding particular positions
    grouped by the first letter of their sort_name - this makes it
    easier to navigate to the person you're looking for. This function
    helps to generate context values for rending such a menu and the
    right positions / people.

    'prefix_letter' should either be a letter of the alphabet (if you
    only want people starting with that letter returned) or None if
    all positions should be returned (no filtering).  This returns
    both that filtered position queryset and a dictionary of helpful
    values for the context for rendering the alphabetic menu.
    """
    extra_context = {}
    extra_context['count_by_prefix'] = \
        positions_count_for_letter(position_qs)
    extra_context['current_name_prefix'] = prefix_letter
    if prefix_letter:
        position_qs = position_qs.filter(
            person__sort_name__istartswith=prefix_letter)
    return position_qs, extra_context

def position_pt(request, pt_slug):
    """Show current positions with a given PositionTitle"""
    return position(request, pt_slug)

def position_pt_ok(request, pt_slug, ok_slug):
    """Show current positions with a given PositionTitle and OrganisationKind"""
    return position(request, pt_slug, ok_slug=ok_slug)

def position_pt_ok_o(request, pt_slug, ok_slug, o_slug):
    """Show current positions with a given PositionTitle, OrganisationKind and Organisation"""
    return position(request, pt_slug, ok_slug=ok_slug, o_slug=o_slug)


def get_position_type_redirect(pt_slug, ok_slug=None, o_slug=None):
    """If this position type URL should redirect, return the new URL.

    If no redirect is required, return None."""
    pt_redirect = get_slug_redirect(models.PositionTitle, pt_slug)
    ok_redirect = get_slug_redirect(models.OrganisationKind, ok_slug) if ok_slug else None
    o_redirect = get_slug_redirect(models.Organisation, o_slug) if o_slug else None

    new_pt_slug = pt_redirect.slug if pt_redirect else pt_slug
    new_ok_slug = ok_redirect.slug if ok_redirect else ok_slug
    new_o_slug = o_redirect.slug if o_redirect else o_slug

    if o_slug:
        if pt_redirect or ok_redirect or o_redirect:
            return reverse(
                'position_pt_ok_o',
                kwargs={
                    'pt_slug': new_pt_slug,
                    'ok_slug': new_ok_slug,
                    'o_slug': new_o_slug,
                    })
    elif ok_slug:
        if pt_redirect or ok_redirect:
            return reverse(
                'position_pt_ok',
                kwargs={
                    'pt_slug': new_pt_slug,
                    'ok_slug': new_ok_slug,
                    }
                )
    else:
        if pt_redirect:
            return reverse(
                'position_pt',
                kwargs={
                    'pt_slug': new_pt_slug
                    }
                )


def position(request, pt_slug, ok_slug=None, o_slug=None):
    new_url = get_position_type_redirect(pt_slug, ok_slug, o_slug)
    if new_url:
        return redirect(new_url)

    title = get_object_or_404(
        models.PositionTitle,
        slug=pt_slug
    )

    # If this position title is one associated with any parliamentary
    # session, show alternative parliamentary sessions:
    possible_sessions = []
    if models.ParliamentarySession.objects.filter(
            position_title=title
    ).exists():
        possible_sessions = models.ParliamentarySession.objects.order_by('name')

    page_title = title.name
    organisation = None
    organisation_kind = None
    if o_slug:
        organisation = get_object_or_404(models.Organisation,
                                         slug=o_slug)
        page_title += " of " + organisation.name
    elif ok_slug:
        organisation_kind = get_object_or_404(models.OrganisationKind,
                                              slug=ok_slug)
        page_title += " of any " + organisation_kind.name

    session = None
    session_slug = request.GET.get('session')
    if session_slug:
        session = get_object_or_404(
            models.ParliamentarySession,
            slug=session_slug
        )
    # Build up context data for the links to switch between particular
    # parliamentary sessions and all current position holders:
    session_details = []
    for s in [None] + list(possible_sessions):
        if session != s:
            params = request.GET.copy()
            if s is None:
                session_filter = 'Current'
                params.pop('session', None)
                override = override_current_session(session)
                if override is None:
                    path = request.path
                else:
                    path = override.positions_url()
            else:
                session_filter = s.name
                params['session'] = s.slug
                path = s.positions_url()
            session_details.append({
                'url': path + '?' + params.urlencode(),
                'name': session_filter,
                'session': s,
                'should_link': session != s,
            })

    # If a particular parliamentary session has been requested, only
    # return positions that overlap with the period of that
    # session. Otherwise only return currently active positions.
    if session:
        positions = title.position_set.overlapping_dates(
            session.start_date, session.end_date
        )
    else:
        positions = title.position_set.all().currently_active()
    if ok_slug is not None:
        positions = positions.filter(organisation__kind__slug=ok_slug)
    if o_slug is not None:
        positions = positions.filter(organisation__slug=o_slug)

    # Order by place name unless ordering by person name is requested:
    order = 'place'
    if request.GET.get('order') == 'name':
        order = 'person__sort_name'
    positions = positions.order_by(order)

    positions = positions.select_related('person',
                                         'organisation',
                                         'title',
                                         'place',
                                         'place__kind',
                                         'place__parent_place')

    place_slug = request.GET.get('place_slug')
    if place_slug:
        positions = positions.filter(
            Q(place__slug=place_slug) | Q(place__parent_place__slug=place_slug)
        )

    # see if we should show the grid
    view = request.GET.get('view', 'list')

    if view == 'grid':
        template = 'core/position_detail_grid.html'
        places   = [] # not relevant to this view
    else:
        template = 'core/position_detail.html'

        # Collect all the places those positions refer to:
        child_places = sorted(set(x.place for x in positions if x.place),
                              key=lambda p: p.name)

        # Extract the parents of those places as well:
        parent_place_ids = [x.parent_place.id for x in child_places if (x and x.parent_place)]
        parent_places = models.Place.objects.filter(id__in=parent_place_ids).select_related('kind')

        # combine the places into a single list for the search drop down
        places = []
        places.extend(parent_places)
        places.extend(child_places)

    context = {
        'object':     title,
        'page_title': page_title,
        'order':      request.GET.get('order'),
        'organisation_kind':   organisation_kind,
        'org':        organisation,
        'places':     places,
        'place_slug': place_slug,
        'session': session,
        'session_details': session_details,
    }

    if request.GET.get('a') == '1':
        positions, extra_context = filter_by_alphabet(
            request.GET.get('letter'), positions)
        context.update(extra_context)
        context['alphabetical_link_from_query_parameter'] = True
    context['positions'] = positions

    if request.GET.get('format') == 'csv':

        response = HttpResponse(content_type='text/csv')

        writer = csv.writer(response)

        writer.writerow([
            'id',
            'source',
            'name',
            'honorific_prefix',
            'email',
            'image',
            'identifier__wikidata',
            'party',
            'party_wikidata_id',
            'area',
            'area_wikidata_id',
            'start_date',
            'end_date'
        ])

        for position in positions:

            person = position.person

            person_wikidata_id_query = person.identifiers.filter(scheme='wikidata')
            if person_wikidata_id_query.exists():
                person_wikidata_id = person_wikidata_id_query.first().identifier
            else:
                person_wikidata_id = None

            email_query = person.contacts.filter(kind__slug='email').order_by('-preferred')
            if email_query.exists():
                email = email_query.first().value
            else:
                email = None

            if person.parties_and_coalitions():
                if len(person.parties_and_coalitions()) > 1:
                    person_party_name = 'MULTIPLE'
                    person_party_wikidata_id = 'MULTIPLE'
                else:
                    party = person.parties_and_coalitions().first()
                    person_party_name = party.name
                    person_party_wikidata_id_query = party.identifiers.filter(scheme='wikidata')
                    if person_party_wikidata_id_query.exists():
                        person_party_wikidata_id = person_party_wikidata_id_query.first().identifier
                    else:
                        person_party_wikidata_id = None
            else:
                person_party_name = None
                person_party_wikidata_id = None

            if person.constituencies():
                if len(person.constituencies()) > 1:
                    person_area_name = 'MULTIPLE'
                    person_area_wikidata_id = 'MULTIPLE'
                else:
                    area = person.constituencies().first()
                    person_area_name = area.name
                    person_area_wikidata_id_query = area.identifiers.filter(scheme='wikidata')
                    if person_area_wikidata_id_query.exists():
                        person_area_wikidata_id = person_area_wikidata_id_query.first().identifier
                    else:
                        person_area_wikidata_id = None
            else:
                person_area_name = None
                person_area_wikidata_id = None

            def handle_approx_date(date):
                return_date = None
                if date and not date.future:
                    if date.year:
                        return_date = str(date.year)
                    if date.month:
                        return_date = return_date + '-' + str(date.month).zfill(2)
                    if date.day:
                        return_date = return_date + '-' + str(date.day).zfill(2)

                return return_date

            writer.writerow([
                person.slug,
                request.build_absolute_uri(person.get_absolute_url())
                            .replace('http://', 'https://'),
                person.name,
                person.honorific_prefix,
                email,
                request.build_absolute_uri('/' + str(person.primary_image()))
                            .replace('http://', 'https://'),
                person_wikidata_id,
                person_party_name,
                person_party_wikidata_id,
                person_area_name,
                person_area_wikidata_id,
                handle_approx_date(position.start_date),
                handle_approx_date(position.end_date)
            ])

        return response

    else:

        return render_to_response(
            template,
            context,
            context_instance=RequestContext(request)
        )


class OrganisationDetailView(SlugRedirectMixin, BaseDetailView):
    model = models.Organisation

    def get_context_data(self, **kwargs):
        context = super(OrganisationDetailView, self).get_context_data(**kwargs)
        context['positions'] = self.object.position_set. \
            select_related('person', 'title', 'place'). \
            prefetch_related('person__alternative_names', 'person__images'). \
            order_by('person__legal_name')
        return context


class OrganisationDetailSub(SubSlugRedirectMixin, BaseDetailView):
    model = models.Organisation
    sub_page = None

    def get_template_names(self):
        return ["core/organisation_%s.html" % self.sub_page]

    def get_context_data(self, **kwargs):
        context = super(OrganisationDetailSub, self).get_context_data(**kwargs)
        # Allow the order that people are listed on the 'people' sub-page
        # of an organisation to be controlled with the 'order' query
        # parameter:

        if self.sub_page == 'people':
            all_positions = context['all_positions'] = \
                self.object.position_set.filter(person__hidden=False). \
                    select_related('person', 'title', 'place'). \
                    prefetch_related('person__alternative_names', 'person__images')

            if self.request.GET.get('all'):
                positions = all_positions
            # Limit to those currently active, or inactive
            elif self.request.GET.get('historic'):
                context['historic'] = True
                positions = all_positions.currently_inactive()
            else:
                context['historic'] = False
                positions = all_positions.currently_active()

            if self.request.GET.get('order') == 'place':
                context['sorted_positions'] = positions.order_by_place()
            else:
                context['sorted_positions'] = positions.order_by_person_name()
        return context

class OrganisationKindList(SlugRedirectMixin, SingleObjectMixin, ListView):
    model = models.OrganisationKind

    def get_queryset(self):
        self.object = self.get_object(queryset=self.model.objects.all())
        orgs = (
            self.object
                .organisation_set
                .all()
                .annotate(num_position_holders=Count('position'))
                .order_by('-num_position_holders', 'name')
        )
        return orgs

    def get_context_data(self, **kwargs):
        context = super(OrganisationKindList, self).get_context_data(**kwargs)
        context['kind'] = self.object
        return context

def parties(request):
    """Show all parties that currently have MPs sitting in parliament"""

    parties = models.Organisation.objects.all().active_parties()

    return render_to_response(
        'core/parties.html',
        {
            'parties': parties,
        },
        context_instance = RequestContext( request ),
    )

def featured_person(request, current_slug, direction):
    """Show featured mp either before or after the current one.
       Returns a random person if current slug doesn't match, although numeric
       slugs are consistent to ease the caching a little (so javascript can make
       random requests that can be cached)."""
    want_previous = direction == 'before'
    featured_person = models.Person.objects.get_next_featured(current_slug, want_previous)
    return render_to_response(
        'core/person_feature.html',
        {
            'featured_person': featured_person,
        },
        context_instance = RequestContext( request ),
    )

# We never want this to be cached
@never_cache
def memcached_status(request):
    """Helper view that let's us check that the values are being stored in the cache, and subsequently purged"""

    cache_key = 'memcached_status'
    now = calendar.timegm( time.gmtime() )
    ttl = 10

    cached = cache.get(cache_key)

    if cached:
        response = "Found %u in cache with key %s, which was %u seconds ago (ttl is %u seconds)" % (cached, cache_key, now - cached, ttl )
    else:
        cache.set( cache_key, now, ttl )
        response = "Value not found in cache with key %s - added %u for %u seconds" % ( cache_key, now, ttl )

    return HttpResponse(
        response,
        content_type='text/plain',
    )


# Template the robots.txt so we can block robots on staging.
@cache_control(max_age=86400, s_maxage=86400, public=True)
def robots(request):
    return render_to_response(
        'robots.txt',
        {
            'staging': settings.STAGING,
        },
        context_instance=RequestContext(request),
        content_type='text/plain',
    )


class VersionView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        result = {
            'python_version': sys.version,
            'django_version': django.get_version(),
        }
        # Try to get the object name of HEAD from git:
        try:
            git_version = subprocess.check_output(
                ['git', 'rev-parse', '--verify', 'HEAD'],
                cwd=dirname(__file__),
            ).strip()
            result['git_version'] = git_version
        except OSError, subprocess.CalledProcessError:
            pass
        return HttpResponse(
            json.dumps(result), content_type='application/json'
        )


class SessionListView(ListView):

    model = models.ParliamentarySession
    template_name = 'core/session_list.html'

    def get_ordering(self):
        return ('-start_date', '-end_date', 'name')
