import re
import urllib2
import time
import calendar

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
    return render_to_response(
        'home.html',
        {
          'featured_person': featured_person,
        },
        context_instance=RequestContext(request)
    )

def organisation_list(request):
    return object_list(
        request,
        queryset=models.Organisation.objects.all(),
    )

def person(request, slug):
    return object_detail(
        request,
        queryset = models.Person.objects,
        slug     = slug,
    )

def person_scorecard(request, slug):
    return object_detail(
        request,
        queryset      = models.Person.objects,
        template_name = "core/person_scorecard.html",
        slug          = slug,
    )

class PlaceDetailView(DetailView):
    model = models.Place

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PlaceDetailView, self).get_context_data(**kwargs)
        context['place_type_count'] = models.Place.objects.filter(kind=self.object.kind).count()
        return context


def place_kind(request, slug=None):

    if slug and slug != 'all':
        kind = get_object_or_404(
            models.PlaceKind,
            slug=slug
        )
        queryset = kind.place_set.all()
    else:
        kind = None
        queryset = models.Place.objects.all()

    return object_list(
        request,
        queryset = queryset,
        extra_context = {
            'kind':       kind,
            'all_kinds':  models.PlaceKind.objects.all(),
        },
    )

def place_mapit_area(request, mapit_id):

    place = get_object_or_404(
        models.Place,
        mapit_area=mapit_id
    )

    return redirect(place)

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
        child_places = [x.place for x in positions.distinct('place').order_by('place__name')]
        
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


# We really want this to be cached
@cache_control(max_age=300, s_maxage=300, public=True)
def twitter_feed(request):

    # for now ignore the screen name that we get sent.
    twitter_name = settings.TWITTER_ACCOUNT_NAME

    # If we don't have a twitter name we can't fetch it
    if not twitter_name:
        raise Http404

    # get the json from the cache, or fetch it if needed
    cache_key = twitter_name + '-twitter-feed'
    json = cache.get(cache_key)

    if not json:
        json = urllib2.urlopen('http://api.twitter.com/1/statuses/user_timeline.json?screen_name='+twitter_name+'&count=4').read()
        cache.set( cache_key, json, 300 )

    return HttpResponse(
        json,
        content_type='application/json',
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
        response = "Found %u in cache, which was %u seconds ago (ttl is %u seconds)" % (cached, now - cached, ttl )
    else:
        cache.set( cache_key, now, ttl )
        response = "Value not found in cache - added %u for %u seconds" % ( now, ttl )
    
    return HttpResponse(
        response,
        content_type='text/plain',
    )

    
