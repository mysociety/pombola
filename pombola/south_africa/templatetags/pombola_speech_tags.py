import re

from django import template
from django.core.urlresolvers import reverse

from speeches.models import Speaker
from pombola.core.models import Identifier, Person, ContentType

register = template.Library()

@register.filter
def person_url(speaker):
    # see also views.py SAPersonDetail

    try:
        popit_id = speaker.person.popit_id
        [scheme, identifier] = re.match('(.*?)(/.*)$', popit_id).groups()
        i = Identifier.objects.get(
            content_type = ContentType.objects.get_for_model(Person),
            scheme = scheme,
            identifier = identifier,
        )
        person = Person.objects.get(id=i.object_id)
        return reverse('person', args=(person.slug,))

    except Exception as e:
        return e
        # return None
