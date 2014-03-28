# modified from http://djangosnippets.org/snippets/656/

from django.template import Library
from django.utils.safestring import mark_safe
from django.core.urlresolvers import resolve, Resolver404
from django.conf import settings
import re
from urlparse import urlparse

register = Library()

url_name_mappings = settings.BREADCRUMB_URL_NAME_MAPPINGS

separator = '  <span class="sep">&raquo;</span> ';
hansard_part = 'hansard/'

def slash_stripped_path_from_url(url):
    '''Extract the path from the URL, with leading and trailing / stripped

    >>> slash_stripped_path_from_url('http://localhost:8000/hansard/sitting/whatever/?foo=bar')
    'hansard/sitting/whatever'
    '''
    return urlparse(url).path.strip('/')

def assemble_list_items(links_html, in_li_separator=''):
    '''Take an array strings and wrap them in <li>s with internal separators

    The "internal separator" (in_li_separator) shouldn't appear in the
    last <li>, but should be the last thing in any prevous one.

    >>> assemble_list_items(['hello', '<a href="foo">bar</a>', 'bye'], ' AND')
    '<li>hello AND</li><li><a href="foo">bar</a> AND</li><li>bye</li>'
    >>> assemble_list_items(['baz', 'quux'], ',')
    '<li>baz,</li><li>quux</li>'
    >>> assemble_list_items(['something'], ' AND')
    '<li>something</li>'
    '''
    # The separator shouldn't be added to the last item:
    with_separators = [l + in_li_separator for l in links_html[:-1]]
    with_separators.append(links_html[-1])
    return "".join('<li>{0}</li>'.format(p) for p in with_separators)

def linkify(sub_link, this_url):
    try:
        # Check that this_url can be found in the URLconf:
        resolve(this_url)
        return '<a href="%s" title="Breadcrumb link to %s">%s</a>' % (this_url, sub_link, sub_link)
    except Resolver404:
        return sub_link

@register.filter
def breadcrumbs(url):
    bare_url = slash_stripped_path_from_url(url)
    # If that's empty, immediately return just the home link:
    if not bare_url:
        return '<li>Home</li>'
    if bare_url.startswith(hansard_part):
        bare_url = hansard_part + bare_url[len(hansard_part):].replace('/',' : ')
    links = [l for l in bare_url.split('/') if l]
    bread = []
    if len(links) > 2 and links[1] == 'is':
      # (Organisation|Place|etc.)Kind links like /organization/is/house/
      # (drop it)
      links[1:2] = []
    if links[-1] == 'all': # if links ends with 'all', drop it
      links = links[:-1]

    links_html = ['<a href="/" title="Breadcrumb link to the homepage.">Home</a>']

    seen_links = set()

    for i, link in enumerate(links):

        # FIXME: Why is this required? In what situations do we end up
        # with repeated path elements where we'd want to remove them?
        # If this is important there should be a test that covers it.
        # It was introduced in ee8aa752 referencing #354, but neither
        # gives an example.  n.b. if it is still needed, then from
        # Python 2.7 onwards we could just use collections.OrderedDict
        if link in seen_links:
            continue
        else:
            seen_links.add(link)

        bread.append(link)

        if link in url_name_mappings:
            sub_link, this_url = url_name_mappings[link]
        elif re.match(r'^[\d\-\.,]+$', link):
            # eg '-1.23,4.56'
            sub_link = link
            sub_link = re.sub(r',\s*', ', ', sub_link)
        else:
            sub_link = re.sub('[_\-]', ' ', link).title()
            sub_link = re.sub('\\bFaq\\b', 'FAQ', sub_link)
            this_url = "/{0}/".format("/".join(bread))

        # Never try to link the last element, since it should
        # represent the current page:
        if i == len(links) - 1:
            tlink = sub_link
        else:
            tlink = linkify(sub_link, this_url)

        links_html.append(tlink)
    return mark_safe(assemble_list_items(links_html, separator))
