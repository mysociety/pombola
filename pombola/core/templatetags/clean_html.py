from lxml.etree import LxmlError
from lxml.html.clean import Cleaner

from django.template import Library

register = Library()

@register.filter
def as_clean_html(value):
    try:
        return Cleaner(style=True, scripts=True).clean_html(value.strip())
    except LxmlError:
        return '<p></p>'
