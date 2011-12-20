import re

from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.utils import simplejson

from mzalendo.helpers import geocode

from core import models

from haystack.query import SearchQuerySet

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
        'search/location.html',
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
    
