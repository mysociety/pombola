from lxml.html.clean import Cleaner

from django.template import Library

register = Library()

@register.filter
def as_clean_html(value):
    cleaner = Cleaner(style=True, scripts=True)
    return cleaner.clean_html(value)
