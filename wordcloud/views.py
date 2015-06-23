import os

from django.http import HttpResponse
from django.utils import simplejson
from django.conf import settings

from .wordcloud import popular_words


def wordcloud(request, max_entries=30):
    """ Return tag cloud JSON results"""
    cache_path = settings.WORDCLOUD_CACHE_PATH
    if os.path.exists(cache_path):
        with open(cache_path) as cached_file:
            content = cached_file.read()
    else:
        content = simplejson.dumps(popular_words(max_entries=max_entries))

    return HttpResponse(
        content,
        mimetype='application/json',
        )
