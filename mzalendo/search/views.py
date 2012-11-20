import re

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
  
# normal english stop words to ignore
stopwords = ["'tis", "'t was", "a", "able","about", "across", "after", 
             "ain't","all", "almost", "also", "am", "among", "an", "and",   
            "any", "are", "aren't", "as", "at", "be", "because", "been", "but",  
            "by", "can", "can't", "cannot", "could", "could've", "couldn't", 
            "dear", "did", "didn't", "do", "does", "doesn't", "don't", "either", 
            "else", "ever", "every", "for", "from", "get", "got", "had", "has", "hasn't",
            "have", "he", "he'd", "he'll", "he's", "her", "hers", "him", "his", "how", "how'd",
            "how'll", "how's", "however", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
            "is", "isn't", "it", "it's", "its", "just", "least", "let", "like", "likely", "may", "me",
            "might", "might've", "mightn't", "most", "must", "must've", "mustn't", "my", "neither",
            "no", "nor", "not", "of", "off", "often", "on", "only", "or", "other", "our", "own", "rather",
            "said", "say", "says", "shan't", "she", "she'd", "she'll", "she's", "should", "should've", 
            "shouldn't", "since", "so", "some", "than", "that", "that'll", "that's", "the", "their", "them", 
            "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "tis",
            "to", "too", "twas", "us", "wants", "was", "wasn't", "we", "we'd", "we'll", "we're", "were", "weren't", "what",
            "what'd", "what's", "when", "when", "when'd", "when'll", "when's", "where", "where'd", "where'll", "where's",
            "which", "while", "who", "who'd", "who'll", "who's", "whom", "why", "why'd", "why'll", 
            "why's", "will", "with", "won't", "would", "would've", "wouldn't", "yet", "you", "you'd",
            "you'll", "you're", "you've", "your","shall","very"]

STOP_WORDS = ["a", "able", "about", "above", "abst", "accordance", "according", 
              "accordingly", "across", "act", "actually", "added", "adj", 
              "affected", "affecting", "affects", "after", "afterwards", 
              "again", "against", "ah", "all", "almost", "alone", "along", 
              "already", "also", "although", "always", "am", "among", 
              "amongst", "an", "and", "announce", "another", "any", "anybody",
              "anyhow", "anymore", "anyone", "anything", "anyway", "anyways", 
              "anywhere", "apparently", "approximately", "are", "aren", "arent", 
              "arise", "around", "as", "aside", "ask", "asking", "at", "auth", 
              "available", "away", "awfully", "b", "back", "be", "became", 
              "because", "become", "becomes", "becoming", "been", "before", 
              "beforehand", "begin", "beginning", "beginnings", "begins", "behind", 
              "being", "believe", "below", "beside", "besides", "between", "beyond", 
              "biol", "both", "brief", "briefly", "but", "by", "c", "ca", "came", "can", 
              "cannot", "can't", "cause", "causes", "certain", "certainly", "co", "com", 
              "come", "comes", "contain", "containing", "contains", "could", "couldnt", 
              "d", "date", "did", "didn't", "different", "do", "does", "doesn't", 
              "doing", "done", "don't", "down", "downwards", "due", "during", "e", 
              "each", "ed", "edu", "effect", "eg", "eight", "eighty", "either", "else", 
              "elsewhere", "end", "ending", "enough", "especially", "et", "et-al", 
              "etc", "even", "ever", "every", "everybody", "everyone", "everything", 
              "everywhere", "ex", "except", "f", "far", "few", "ff", "fifth", "first", 
              "five", "fix", "followed", "following", "follows", "for", "former", 
              "formerly", "forth", "found", "four", "from", "further", "furthermore", 
              "g", "gave", "get", "gets", "getting", "give", "given", "gives", "giving", 
              "go", "goes", "gone", "got", "gotten", "h", "had", "happens", "hardly", 
              "has", "hasn't", "have", "haven't", "having", "he", "hed", "hence", "her",
              "here", "hereafter", "hereby", "herein", "heres", "hereupon", "hers", 
              "herself", "hes", "hi", "hid", "him", "himself", "his", "hither", "home", 
              "how", "howbeit", "however", "hundred", "i", "id", "ie", "if", "i'll", 
              "im", "immediate", "immediately", "importance", "important", "in", "inc", 
              "indeed", "index", "information", "instead", "into", "invention", "inward", 
              "is", "isn't", "it", "itd", "it'll", "its", "itself", "i've", "j", "just", "k", 
              "keep", "    keeps", "kept", "kg", "km", "know", "known", "knows", "l", 
              "largely", "last", "lately", "later", "latter", "latterly", "least", 
              "less", "lest", "let", "lets", "like", "liked", "likely", "line", 
              "little", "'ll", "look", "looking", "looks", "ltd", "m", "made", "mainly", 
              "make", "makes", "many", "may", "maybe", "me", "mean", "means", "meantime", 
              "meanwhile", "merely", "mg", "might", "million", "miss", "ml", "more", "moreover", 
              "most", "mostly", "mr", "mrs", "much", "mug", "must", "my", "myself", "n",
              "na", "name", "namely", "nay", "nd", "near", "nearly", "necessarily", 
              "necessary", "need", "needs", "neither", "never", "nevertheless", "new", 
              "next", "nine", "ninety", "no", "nobody", "non", "none", "nonetheless", "noone", 
              "nor", "normally", "nos", "not", "noted", "nothing", "now", "nowhere", "o", "obtain", 
              "obtained", "obviously", "of", "off", "often", "oh", "ok", "okay", "old", "omitted", 
              "on", "once", "one", "ones", "only", "onto", "or", "ord", "other", "others", "otherwise", 
              "ought", "our", "ours", "ourselves", "out", "outside", "over", "overall", "owing", "own", "p", 
              "page", "pages", "part", "particular", "particularly", "past", "per", "perhaps", "placed", 
              "please", "plus", "poorly", "possible", "possibly", "potentially", "pp", "predominantly", 
              "present", "previously", "primarily", "probably", "promptly", "proud", "provides", "put", 
              "q", "que", "quickly", "quite", "qv", "r", "ran", "rather", "rd", "re", "readily", "really", 
              "recent", "recently", "ref", "refs", "regarding", "regardless", "regards", "related", 
              "relatively", "research", "respectively", "resulted", "resulting", "results", "right", 
              "run", "s", "said", "same", "saw", "say", "saying", "says", "sec", "section", "see", "seeing", 
              "seem", "seemed", "seeming", "seems", "seen", "self", "selves", "sent", "seven", "several", "shall", 
              "she", "shed", "she'll", "shes", "should", "shouldn't", "show", "showed", "shown", "showns", "shows", 
              "significant", "significantly", "similar", "similarly", "since", "six", "slightly", "so", "some", 
              "somebody", "somehow", "someone", "somethan", "something", "sometime", "sometimes", "somewhat", 
              "somewhere", "soon", "sorry", "specifically", "specified", "specify", "specifying", "still", 
              "stop", "strongly", "sub", "substantially", "successfully", "such", "sufficiently", "suggest", 
              "sup", "sure", "    t", "take", "taken", "taking", "tell", "tends", "th", "than", "thank", 
              "thanks", "thanx", "that", "that'll", "thats", "that've", "the", "their", "theirs", "them", 
              "themselves", "then", "thence", "there", "thereafter", "thereby", "thered", "therefore", "therein", 
              "there'll", "thereof", "therere", "theres", "thereto", "thereupon", "there've", "these", "they", 
              "theyd", "they'll", "theyre", "they've", "think", "this", "those", "thou", "though", "thoughh", 
              "thousand", "throug", "through", "throughout", "thru", "thus", "til", "tip", "to", "together", 
              "too", "took", "toward", "towards", "tried", "tries", "truly", "try", "trying", "ts", "twice", 
              "two", "u", "un", "under", "unfortunately", "unless", "unlike", "unlikely", "until", "unto", "up", 
              "upon", "ups", "us", "use", "used", "useful", "usefully", "usefulness", "uses", "using", "usually", "v", 
              "value", "various", "'ve", "very", "via", "viz", "vol", "vols", "vs", "w", "want", "wants", "was", "wasn't", 
              "way", "we", "wed", "welcome", "we'll", "went", "were", "weren't", "we've", "what", "whatever", "what'll", 
              "whats", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "wheres", 
              "whereupon", "wherever", "whether", "which", "while", "whim", "whither", "who", "whod", "whoever", "whole", 
              "who'll", "whom", "whomever", "whos", "whose", "why", "widely", "willing", "wish", "with", "within", "without", 
              "won't", "words", "world", "would", "wouldn't", "www", "x", "y", "yes", "yet", "you", "youd", "you'll", "your", 
              "youre", "yours", "yourself", "yourselves", "you've", "z", "zero"]

# hansard-centric words to ignore
hansard_words = ['mr', 'mrs', 'minister', 'speaker', 'madam', 'delete', 
                 'insert', 'hon', 'think', 'committee', '-', 'clause',
                 'sub-clause', 'bill', 'question', 'house', 'members', 
                 'member', 'well', 'will']

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
                if not cleanx in STOP_WORDS and not cleanx in hansard_words:
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


