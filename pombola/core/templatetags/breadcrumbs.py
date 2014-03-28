# modified from http://djangosnippets.org/snippets/656/

from django.template import Library
from django.utils.safestring import mark_safe
from django.core.urlresolvers import resolve, Resolver404
from django.conf import settings
import re
from urlparse import urlparse

register = Library()

url_name_mappings = settings.BREADCRUMB_URL_NAME_MAPPINGS

separator = ' <span class="sep">&raquo;</span> ';
hansard_part = 'hansard/'

def slash_stripped_path_from_url(url):
    '''Extract the path from the URL, with leading and trailing / stripped

    >>> slash_stripped_path_from_url('http://localhost:8000/hansard/sitting/whatever/?foo=bar')
    'hansard/sitting/whatever'
    '''
    return urlparse(url).path.strip('/')

@register.filter
def breadcrumbs(url):
    bare_url = slash_stripped_path_from_url(url)
    # If that's empty, immediately return just the home link:
    if not bare_url:
        return '<li>Home</li>'
    if bare_url.startswith(hansard_part):
        bare_url = hansard_part + bare_url[len(hansard_part):].replace('/',' : ')
    links = bare_url.split('/')
    bread = []
    total = len(links)-1
    if total > 1 and links[1] == 'is':
      # (Organisation|Place|etc.)Kind links like /organization/is/house/
      # (drop it)
      links[1:2] = []
      total -= 1
    if links[total] == 'all': # if links ends with 'all', drop it
      links = links[0:total]
      total -= 1

    home = ['<li><a href="/" title="Breadcrumb link to the homepage.">Home</a> %s </li>' % separator]

    seen_links = {}

    for i, link in enumerate(links):

        if seen_links.get(link):
            continue
        else:
            seen_links[link] = True

        if not link == '':
            bread.append(link)
            if link in url_name_mappings:
                (sub_link, this_url) = url_name_mappings[link]
            elif re.match(r'^[\d\-\.,]+$', link):
                # eg '-1.23,4.56'
                sub_link = link
                sub_link = re.sub(r',\s*', ', ', sub_link)
            else:
                sub_link = re.sub('[_\-]', ' ', link).title()
                sub_link = re.sub('\\bFaq\\b', 'FAQ', sub_link)
                this_url = "/{0}/".format("/".join(bread))
            if not i == total:
                try:
                    resolve(this_url)
                    tlink = '<li><a href="%s" title="Breadcrumb link to %s">%s</a> %s</li>' % (this_url, sub_link, sub_link, separator)
                except Resolver404:
                    tlink = '<li>%s %s</li>' % (sub_link, separator)

            else:
                tlink = '<li>%s</li>' % sub_link
            home.append(tlink)
    return mark_safe("".join(home))
