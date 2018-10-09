# Adapted from https://gist.github.com/mnazim/1073637
from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def active_class(request_path, name, **kwargs):
    """ Return jQuery UI active classes if current request.path is same as name

    Keyword aruguments:
    request  -- Django request object
    name     -- name of the url
    kwargs   -- any kwargs that this route needs
    """
    path = reverse(name, kwargs=kwargs)

    if request_path == path:
        return ' ui-tabs-active ui-state-active '

    return ''
