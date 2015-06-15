from django.http import HttpResponse
from django.utils import simplejson

from .tagcloud import popular_words


def tagcloud(request, n=30):
    """ Return tag cloud JSON results"""
    return HttpResponse(
        simplejson.dumps(popular_words()),
        mimetype='application/json'
    )


