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
    subdir = 'wordcloud_cache'
    cache_path = os.path.join(
        settings.MEDIA_ROOT, subdir, leaf_name
    )
    if os.path.exists(cache_path):
        response = HttpResponse(json.dumps({
            'error':
            ("If you can see this, then X-SendFile (for Apache) or "
             "X-Accel-Redirect (for Nginx) isn't set up correctly in "
             "your webserver's configuration.")
        }))
        response['Content-Type'] = 'application/json'
        response['X-Sendfile'] = cache_path.encode('utf-8')
        response['X-Accel-Redirect'] = '/media_root/{0}/{1}'.format(
            subdir, leaf_name
        )
        return response

    content = json.dumps(popular_words(max_entries=max_entries))

    return HttpResponse(
        content,
        content_type='application/json',
    )
