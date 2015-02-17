# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template

register = template.Library()

@register.filter()
def join_blog_post_titles(category_list):
    """Takes a list of categories or tags and returns their names, wrapped in
    left and right double quotes, seperated by commas and with 'and' between
    the penultimate and final items
    """

    l = len(category_list)
    if l == 1:
        return quote(category_list[0].name)
    else:
        return ", ".join(quote(category.name) for category in category_list[:l-1]) \
                + " and " + quote(category_list[l-1].name)

def quote(text):
    "Takes a string and wraps it in left and right double quotes"
    return "“{0}”".format(text)
