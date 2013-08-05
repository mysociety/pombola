from django.shortcuts  import render_to_response
from django.template   import RequestContext

def home(request):
    """Homepage"""

    return render_to_response(
        'map/home.html',
        {},
        context_instance=RequestContext(request)
    )

