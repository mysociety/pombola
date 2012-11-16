import re

from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.utils import simplejson
import datetime

# from mzalendo.helpers import geocode

from core import models

from haystack.query import SearchQuerySet
from mzalendo.hansard import models as hansard_models

# def location_search(request):
#     
#     loc = request.GET.get('loc', '')
# 
#     results = geocode.find(loc) if loc else []
#     
#     # If there is one result find that matching areas for it
#     if len(results) == 1:
#         mapit_areas = geocode.coord_to_areas( results[0]['lat'], results[0]['lng'] )
#         areas = [ models.Place.objects.get(mapit_id=area['mapit_id']) for area in mapit_areas.values() ]
#     else:
#         areas = None
#         
#     return render_to_response(
#         'search/location.html',
#         {
#             'loc': loc,
#             'results': results,
#             'areas': areas,
#         },
#         context_instance = RequestContext( request ),        
#     )


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
            	'label': result.object.name,
            })
    
    # send back the results as JSON
    return HttpResponse(
        simplejson.dumps(response_data),
        mimetype='application/json'
    )
  

def tagcloud(request):
    """ Return tag cloud JSON results"""
    # Build a query based on duration default is 1 month
    #cutoff = datetime.date.today() - datetime.timedelta(weeks=1)
    #sqs  = SearchQuerySet().models(hansard_models.Entry).filter(sitting__start_date>=cuttoff)

    # Generate tag cloud from content of returned entries
    ignore_terms =['and', 'of', 'the','is','to']
    words = {}
    #for entry in sqs.all():
    #    text = entry.object.content
    
    #sample text for testing
    text = "<p>A member of the Gonja ethnic group, specifically from Bole, John Dramani Mahama was born 29 November 1958 in Damingo in the Damango-Daboya constituency of Ghana. He has been President of Ghana since July 2012. He was the Vice President of Ghana from 2009 to 2012, and he took office as President on 24 July 2012 following the death of his predecessor, President John Atta Mills. He was a Member of Parliament from 1997 to 2009 and Minister of Communications from 1998 to 2001.</p><p> Mahama attended Achimota School and then proceeded to Ghana Secondary School (Tamale) and the University of Ghana, Legon, receiving a bachelor's degree in history in 1981 and a postgraduate diploma in communication studies in 1986. Following this, he travelled to the Institute of Social Sciences, Moscow in the then Soviet Union for further studies in a two-year postgraduate programme, specializing in social psychology.He obtained a master's degree in 1988.</p>"
    for x in text.split():
        if x.strip() in ignore_terms:
            pass
        words[x.strip()] = 1 + words.get(x.strip(), 0)
    cloudlist =[]
    for word in words:
        cloudlist.append({"text":word , "weight": words.get(word)})

    # return results
    return HttpResponse(
        simplejson.dumps(cloudlist),
        mimetype='application/json'
    )


