# modified from http://djangosnippets.org/snippets/656/

from django.template import Library
from django.utils.safestring import mark_safe
# import re

register = Library()

url_name_mappings = {
  'info'   : ('Information', '/info'),
  'person' : ('Politicians', '/person/all'),
  'place' : ('Places', '/place/all')
}

@register.filter
def breadcrumbs(url):
    home = ['<li><a href="/" title="Breadcrumb link to the homepage.">Home</a> &raquo;</li>',]
    query_pos = url.find("?")
    bare_url = url
    if query_pos >= 0:
        bare_url = bare_url[0:query_pos]
    links = bare_url.strip('/').split('/')
    bread = []
    total = len(links)-1
    for i, link in enumerate(links):
        if not link == '':
            bread.append(link)
            if link in url_name_mappings:
                (sub_link, this_url) = url_name_mappings[link]
            else:
                sub_link = link
                this_url = "/".join(bread)
            if not i == total:
                tlink = '<li><a href="%s/" title="Breadcrumb link to %s">%s</a> &raquo;</li>' % (this_url, sub_link, sub_link)
            else:
                tlink = '<li>%s</li>' % sub_link
            home.append(tlink)
    bcrumb = "".join(home)
    return mark_safe(bcrumb)