from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404

import pombola.core.models


def in_place(request, slug):

    place = get_object_or_404( pombola.core.models.Place, slug=slug)
    projects = place.project_set

    return render_to_response(
        'projects/in_place.html',
        {
            'place': place,
            'projects': projects,
        },
        context_instance=RequestContext(request)
    )

