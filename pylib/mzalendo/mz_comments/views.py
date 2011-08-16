from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.views.generic.list_detail import object_detail, object_list
from django.db.models import Count

from django.contrib.contenttypes.models import ContentType

def list_for(request, module_name, slug, page=1):
    """Display comments"""

    # retrieve the content_type that we need
    ct = ContentType.objects.get(model=module_name)

    # retrieve the object
    obj = ct.get_object_for_this_type( slug=slug )

    # 

    return render_to_response(
        'comments/list_for.html',
        {
            'object': obj,
        },
        context_instance=RequestContext(request)
    )
