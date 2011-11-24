import re

from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.utils import simplejson
from django.views.generic.list_detail import object_detail, object_list

from mzalendo.core import models
from mzalendo.helpers import geocode

from haystack.query import SearchQuerySet

def home(request):
    """Homepage"""
    return render_to_response(
        'core/home.html',
        {
        },
        context_instance=RequestContext(request)
    )


def person_list(request):
    return object_list(
        request,
        queryset=models.Person.objects.all(),
    )

def place_list(request):
    return object_list(
        request,
        queryset=models.Place.objects.all(),
    )

def organisation_list(request):
    return object_list(
        request,
        queryset=models.Organisation.objects.all(),
    )

def person(request, slug):
    """"""
    return object_detail(
        request,
        queryset = models.Person.objects,
        slug     = slug,
    )


def place(request, slug):
    """"""
    return object_detail(
        request,
        queryset = models.Place.objects,
        slug     = slug,
    )

def place_kind(request, slug):
    """"""
    print slug
    place_kind = get_object_or_404(
        models.PlaceKind,
        slug=slug
    )

    return object_list(
        request,
        queryset = place_kind.place_set.all(),
        extra_context = { 'kind': place_kind, },
    )


def position(request, slug):
    """"""
    
    title = get_object_or_404(
        models.PositionTitle,
        slug=slug
    )
    
    return render_to_response(
        'core/position_detail.html',
        {
            'object': title,
        },
        context_instance=RequestContext(request)
    )


def organisation(request, slug):
    """"""

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
    """"""
    
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


def location_search(request):
    
    loc = request.GET.get('loc', '')

    results = geocode.find(loc) if loc else []
    
    # If there is one result find that matching areas for it
    if len(results) == 1:
        mapit_areas = geocode.coord_to_areas( results[0]['lat'], results[0]['lng'] )
        areas = [ models.Place.objects.get(mapit_id=area['mapit_id']) for area in mapit_areas.values() ]
    else:
        areas = None
        
    return render_to_response(
        'core/location_search.html',
        {
            'loc': loc,
            'results': results,
            'areas': areas,
        },
        context_instance = RequestContext( request ),        
    )


def autocomplete(request):
    """Return autocomple JSON results"""
    
    term = request.GET.get('term','').strip()
    response_data = []

    if len(term):

        # Does not work - probably because the FLAG_PARTIAL is not set on Xapian
        # (trying to set it in settings.py as documented appears to have no effect)
        # sqs = SearchQuerySet().autocomplete(name_auto=term)

        # Split the search term up into little bits
        terms = re.split(r'\s+', term)

        # Build up a query based on the bits
        sqs = SearchQuerySet()        
        for bit in terms:
            # print "Adding '%s' to the '%s' query" % (bit,term)
            sqs = sqs.filter_and(
                name_auto__startswith = sqs.query.clean( bit )
            )

        # collate the results into json for the autocomplete js
        for result in sqs.all()[0:10]:
            response_data.append({
            	'url':   result.object.get_absolute_url(),
            	'label': result.object.name(),
            })
    
    # send back the results as JSON
    return HttpResponse(
        simplejson.dumps(response_data),
        mimetype='application/json'
    )
    
