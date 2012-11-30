import re
import os

from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.utils import simplejson
import datetime
from operator import itemgetter

# from mzalendo.helpers import geocode

from core import models

from haystack.query import SearchQuerySet
from mzalendo.hansard import models as hansard_models



BASEDIR = os.path.dirname(__file__)

# normal english stop words and hansard-centric words to ignore
STOP_WORDS = open(os.path.join(BASEDIR, 'stopwords.txt'), 'rU').read().splitlines()


# def location_search(request):
#     
#     loc = request.GET.get('loc', '')
# 
#     results = geocode.fin(loc) if loc else []
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
  

def latest(n=20):
    Entry = hansard_models.Entry
    # filter = dict(start_date=Entry.objects.order_by('-start_date')[0].s)
    i = max(len(Entry.objects.all()) - n, 0)
    xs = [obj.id for obj in Entry.objects.all()]
    xs = xs[-n:]
    filter = dict(sitting__id__in=xs)
    return SearchQuerySet().models(Entry).all()

def tagcloud(request,wks=4):
    """ Return tag cloud JSON results"""
    # Build a query based on duration default is 1 month
    # cutoff = datetime.date.today() - datetime.timedelta(weeks=int(wks))
    # sqs  = SearchQuerySet().models(Entry).filter(sitting__id__in=[])
    sqs = latest(30)


    cloudlist =[]
    
    try:
        # Generate tag cloud from content of returned entries
        words = {}
        for entry in sqs.all():
            text = entry.object.content
    
            for x in text.lower().split():
                cleanx = x.replace(',','').replace('.','').replace('"','').strip()
                if not cleanx in STOP_WORDS: # and not cleanx in hansard_words:
                    words[cleanx] = 1 + words.get(cleanx, 0)

        for word in words:
            cloudlist.append({"text":word , "weight": words.get(word), "link":"/search/hansard/?q=%s" % word })

        sortedlist = sorted(cloudlist, key=itemgetter('weight'),reverse=True)[:25]
    except:
        sortedlist =[]

    # return results
    return HttpResponse(
        simplejson.dumps(sortedlist),
        mimetype='application/json'
    )


