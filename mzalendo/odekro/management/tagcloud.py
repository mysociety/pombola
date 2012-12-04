import os
from django.utils import simplejson
import datetime
from operator import itemgetter


from core import models

from haystack.query import SearchQuerySet
from mzalendo.hansard import models as hansard_models


BASEDIR = os.path.dirname(__file__)
# normal english stop words and hansard-centric words to ignore
STOP_WORDS = open(os.path.join(BASEDIR, 'stopwords.txt'), 'rU').read().splitlines()



def latest(n=30):
    Entry = hansard_models.Entry
    # filter = dict(start_date=Entry.objects.order_by('-start_date')[0].s)
    i = max(len(Entry.objects.all()) - n, 0)
    xs = [obj.id for obj in Entry.objects.all()]
    xs = xs[-n:]
    filter = dict(sitting__id__in=xs)
    return SearchQuerySet().models(Entry).all()

def tagcloud(n=30):
    """ Return tag cloud JSON results"""
    # Build a query based on fetching the last n hansards
    #cutoff = datetime.date.today() - datetime.timedelta(weeks=int(wks))
    #sqs  = SearchQuerySet().models(hansard_models.Entry).filter(sitting_date__gte=cutoff)
    
    sqs  = SearchQuerySet().models(hansard_models.Entry).all() #filter(sitting__pk__gte=(int(cutoff.pk)-int(wks)))
    sqs = latest(n)


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
    return simplejson.dumps(sortedlist)

