import re
import urllib2
import time
import calendar
import datetime
import random

from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.views.generic.list_detail import object_detail, object_list
from django.views.decorators.cache import cache_control, never_cache
from django.views.generic import ListView, DetailView
from django.core.cache import cache
from django.conf import settings
from django.http import Http404
from django.contrib.contenttypes.models import ContentType

from mzalendo.core import models
from mzalendo.helpers import geocode

def home(request):
    """Homepage"""
    current_slug = False
    if request.GET.get('after'):
        current_slug = request.GET.get('after')
    elif request.GET.get('before'):
        current_slug = request.GET.get('before')
    featured_person = models.Person.objects.get_next_featured(current_slug, request.GET.get('before'))
    
    # for the eletion homepage produce a list of all the featured people. Shuffle it each time to avoid any bias.
    featured_persons = list(models.Person.objects.get_featured())
    random.shuffle(featured_persons)

    return render_to_response(
        'home.html',
        {
          'featured_person':  featured_person,
          'featured_persons': featured_persons,
        },
        context_instance=RequestContext(request)
    )

def organisation_list(request):
    return object_list(
        request,
        queryset=models.Organisation.objects.all(),
    )

def person(request, slug):
    # Check if this is old slug for redirection:
    try:
        sr = models.SlugRedirect.objects.get(content_type=ContentType.objects.get_for_model(models.Person),
                                             old_object_slug=slug)
        return redirect(sr.new_object)
    # Otherwise look up the slug as normal:
    except models.SlugRedirect.DoesNotExist:
        return object_detail(
                request,
                queryset = models.Person.objects,
                slug     = slug,
        )

def person_sub_page(request, slug, sub_page):
    return object_detail(
        request,
        queryset      = models.Person.objects,
        template_name = "core/person_%s.html" % sub_page,
        slug          = slug,
    )

class PlaceDetailView(DetailView):
    model = models.Place

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PlaceDetailView, self).get_context_data(**kwargs)
        context['place_type_count'] = models.Place.objects.filter(kind=self.object.kind).count()
        return context

def place_sub_page(request, slug, sub_page):
    return object_detail(
        request,
        queryset      = models.Place.objects,
        template_name = "core/place_%s.html" % sub_page,
        slug          = slug,
    )

def place_kind(request, slug=None, session_slug=None):

    if slug and slug != 'all':
        kind = get_object_or_404(
            models.PlaceKind,
            slug=slug
        )
        queryset = kind.place_set.all()
    else:
        kind = None
        queryset = models.Place.objects.all()

    if session_slug:
        session = get_object_or_404(
            models.ParliamentarySession,
            slug=session_slug
        )
    else:
        session = None

    # If this is a PlaceKind with parliamentary sessions, but a
    # particular one hasn't been specified, make the default either
    # the current session, or the most recent one if there is no
    # current session.  (This is largely to make any old bookmarked
    # links to (e.g.) /place/is/constituency/ still work.)

    if kind and not session:
        sessions = list(kind.parliamentary_sessions())
        if sessions:
            today = datetime.date.today()
            current_sessions = [s for s in sessions if s.covers_date(today)]
            if current_sessions:
                session = current_sessions[0]
            else:
                session = sessions[-1]

    if queryset and session:
        queryset = queryset.filter(parliamentary_session=session)

    return object_list(
        request,
        queryset = queryset,
        extra_context = {
            'kind':             kind,
            'selected_session': session,
            'all_kinds':        models.PlaceKind.objects.all(),
        },
    )

def place_mapit_area(request, mapit_id):

    place = get_object_or_404(
        models.Place,
        mapit_area=mapit_id
    )

    return redirect('place_election', slug=place.slug)

def position(request, slug):
    title = get_object_or_404(
        models.PositionTitle,
        slug=slug
    )
    
    positions = title.position_set.all().currently_active().order_by('place')
    
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

        # This is an expensive query. Alternative is to have some sort of config that
        # links job titles to relevant place kinds - eg MP :: constituency. Even that
        # would fail for some types of position though.
        child_places = sorted(set(x.place for x in positions.distinct('place').order_by('place__name')))

        # Extract all the parent places too
        parent_places = set(x.parent_place for x in child_places if (x and x.parent_place))
        parent_places = sorted(parent_places, key=lambda item: item.name)

        # combine the places into a single list for the search drop down
        places = []
        places.extend(parent_places)
        places.extend(child_places)


    return render_to_response(
        template,
        {
            'object':     title,
            'positions':  positions,
            'places':     places,
            'place_slug': place_slug,
        },
        context_instance=RequestContext(request)
    )


def organisation(request, slug):
    org = get_object_or_404(
        models.Organisation,
        slug=slug
    )

    return render_to_response(
        'core/organisation_detail.html',
        {
            'object': org,
            'positions': org.position_set.all().order_by('person__legal_name'),
        },
        context_instance=RequestContext(request)
    )

def organisation_sub_page(request, slug, sub_page):
    return object_detail(
        request,
        queryset      = models.Organisation.objects,
        template_name = "core/organisation_%s.html" % sub_page,
        slug          = slug,
    )

def organisation_kind(request, slug):
    org_kind = get_object_or_404(
        models.OrganisationKind,
        slug=slug
    )
    
    orgs = (
        org_kind
            .organisation_set
            .all()
            .annotate(num_positions = Count('position'))
            .order_by('-num_positions', 'name')
    )
    
    return object_list(
        request,
        queryset = orgs,
        extra_context = { 'kind': org_kind, },
    )

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
        context_instance = RequestContext( request ),
        mimetype         = 'text/plain' # will need to change to content_type in Django 1.5
    )
