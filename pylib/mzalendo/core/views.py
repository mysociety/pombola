from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext

def home(request):
    """Homepage"""
    return render_to_response(
        'core/home.html',
        {},
        context_instance=RequestContext(request)
    )

