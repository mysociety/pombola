from django.http import HttpResponse
from django.utils import simplejson

from .wordcloud import popular_words


def wordcloud(request, n=30):
    """ Return tag cloud JSON results"""
    return HttpResponse(
        simplejson.dumps(popular_words()),
        mimetype='application/json'
    )


