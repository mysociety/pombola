from django.http import HttpResponse
from django.utils import simplejson

from .wordcloud import popular_words


def wordcloud(request, max_entries=30):
    """ Return tag cloud JSON results"""
    return HttpResponse(
        simplejson.dumps(popular_words(max_entries=max_entries)),
        mimetype='application/json'
    )


