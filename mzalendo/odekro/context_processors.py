from django.core.urlresolvers import reverse, resolve

from models import MP
from core.models import Person


def process(request):
    rs = resolve(request.path_info)
    if rs.url_name is 'person':
        slug = rs.kwargs['slug']
        
        try:
            person = Person.objects.get(slug=slug)
            return dict(mp=MP.objects.get(person=person))
        except: pass
    return {}


