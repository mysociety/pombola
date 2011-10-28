from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.views.generic.list_detail import object_detail, object_list
from django.db.models import Count

from django.contrib.contenttypes.models import ContentType

def get_object(module_name, slug):
    # retrieve the content_type that we need
    ct = get_object_or_404( ContentType, model=module_name )

    # retrieve the object
    obj = get_object_or_404( ct.model_class(), slug=slug )

    return obj
    

def list_for(request, module_name, slug):
    """Display comments"""

    obj = get_object( module_name, slug )

    return render_to_response(
        'comments/list_for.html',
        {
            'object': obj,
        },
        context_instance=RequestContext(request)
    )

def add(request, module_name, slug):

    obj = get_object( module_name, slug )

    return render_to_response(
        'comments/add.html',
        {
            'object': obj,
        },
        context_instance=RequestContext(request)
    )
