from django import template
# from django.template.loader import render_to_string
# from django.conf import settings
# from django.contrib.contenttypes.models import ContentType
# from django.contrib import comments
# from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def get_comment_list_url(object, page=1):
    """
    Create the url to the comments for the given object.

    Example::
        {{ get_comment_list_url object }}
    """
        
    return reverse(
        'mz_comments.views.list_for',
        kwargs = {
            'slug':    object.slug,
            'module_name': object._meta.module_name,
            'page':  page,
        }
    )

