from django.utils import simplejson

from tag_cloud.tagcloud import popular_words

def tagcloud(max_entries=20):
    return simplejson.dumps(popular_words(max_entries=max_entries))
