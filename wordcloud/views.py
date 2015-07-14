import json
import os

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_page

from .wordcloud import popular_words


@cache_page(60*60*4)
def wordcloud(request, max_entries=30):
    """ Return tag cloud JSON results"""

    max_entries = int(max_entries)
    leaf_name = 'wordcloud-{0}.json'.format(max_entries)
    cache_path = os.path.join(
        settings.MEDIA_ROOT, 'wordcloud_cache', leaf_name
    )
    if os.path.exists(cache_path):
        response = HttpResponse()
        response['Content-Type'] = 'application/json'
        response['X-Sendfile'] = cache_path.encode('utf-8')
        return response

    content = json.dumps(popular_words(max_entries=max_entries))

    return HttpResponse(
        content,
        content_type='application/json',
    )
