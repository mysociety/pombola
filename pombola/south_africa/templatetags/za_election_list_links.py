from django import template
import re

register = template.Library()

@register.filter()
def get_party_slug(org_slug):
    """Takes the original slug of an election list 'organisation' and returns
    the party slug
    """

    re_matches = decompose_slug(org_slug)
    return re_matches.group('party')

@register.filter()
def get_place_slug(org_slug):
    """Takes the original slug of an election list 'organisation'
    and returns the place (province) slug
    (or None if the slug contains no province information)
    """

    re_matches = decompose_slug(org_slug)
    return re_matches.group('place')

def decompose_slug(slug):
    """Returns regexp matches
    """
    election_list_slug_re = re.compile(
        r'''^
        (?P<party>.*)-
        (?P<place_type>provincial|national|regional)-
        (?:(?P<place>.*)-)*
        election-list-
        (?P<year>.*)
        $''',
        re.VERBOSE
    )
    return election_list_slug_re.search(slug)
